import os
import replicate
import mysql.connector
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Replicate para Llama 3
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Configuración de bases de datos
db_configs = {
    "usuarios": {
        "host": "trolley.proxy.rlwy.net",
        "port": 37649,
        "user": "root",
        "password": "ivPrQpJMsVQQVgoHMqvrZwGkmfoBxjjQ",
        "database": "DBusuarios_app"
    },
    "pos": {
        "host": "trolley.proxy.rlwy.net",
        "port": 37649,
        "user": "root",
        "password": "ivPrQpJMsVQQVgoHMqvrZwGkmfoBxjjQ",
        "database": "DBSistemaPOS"
    }
}

class LlamaAgent:
    def __init__(self):
        self.model = "meta/meta-llama-3-8b-instruct:a421be39257c2b5bfdc61e56fa80efb64bcd077cba73c07e5e99431157c4aba2"
        
    def get_db_connection(self, db_name="usuarios"):
        """Obtener conexión a la base de datos MySQL
        
        Args:
            db_name: Nombre de la base de datos a conectar ('usuarios' o 'pos')
        """
        try:
            if db_name not in db_configs:
                print(f"Base de datos {db_name} no configurada")
                return None
                
            conn = mysql.connector.connect(**db_configs[db_name])
            return conn
        except mysql.connector.Error as err:
            print(f"Error de conexión a la base de datos: {err}")
            return None
    
    def get_db_schema(self, db_name="usuarios"):
        """Obtener el esquema de la base de datos
        
        Args:
            db_name: Nombre de la base de datos ('usuarios' o 'pos')
        """
        try:
            conn = self.get_db_connection(db_name)
            if not conn:
                return "No se pudo conectar a la base de datos."
                
            cursor = conn.cursor()
            
            # Obtener todas las tablas
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            schema = f"Esquema de la base de datos {db_configs[db_name]['database']}:\n\n"
            
            # Obtener estructura de cada tabla
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                schema += f"Tabla '{table_name}':\n"
                for column in columns:
                    schema += f"- {column[0]}: {column[1]}"
                    if column[3] == "PRI":
                        schema += " (clave primaria)"
                    elif column[3] == "UNI":
                        schema += " (único)"
                    schema += "\n"
                schema += "\n"
            
            cursor.close()
            conn.close()
            
            return schema
        except mysql.connector.Error as err:
            print(f"Error al obtener el esquema: {err}")
            return f"Error al obtener el esquema: {err}"
            
    def execute_query(self, query, db_name="usuarios"):
        """Ejecutar una consulta SQL en la base de datos
        
        Args:
            query: Consulta SQL a ejecutar
            db_name: Nombre de la base de datos ('usuarios' o 'pos')
        """
        try:
            conn = self.get_db_connection(db_name)
            if not conn:
                return None
                
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except mysql.connector.Error as err:
            print(f"Error al ejecutar la consulta: {err}")
            return None
            
    def format_query_results(self, results):
        """Formatear los resultados de la consulta para la respuesta"""
        if not results:
            return "No se encontraron resultados para esta consulta."
            
        # Formatear los resultados como texto
        formatted_results = ""
        for i, row in enumerate(results):
            formatted_results += f"Registro {i+1}:\n"
            for key, value in row.items():
                formatted_results += f"  {key}: {value}\n"
            formatted_results += "\n"
            
        return formatted_results
    
    def generate_sql_query(self, user_question):
        """Generar una consulta SQL a partir de la pregunta del usuario utilizando Llama 3"""
        try:
            # Obtener información de esquema de ambas bases de datos
            usuarios_schema = self.get_db_schema("usuarios")
            pos_schema = self.get_db_schema("pos")
            
            # Contexto para el modelo
            system_prompt = f"""
            Eres un asistente experto en SQL que convierte preguntas en consultas SQL precisas para MySQL.
            Las bases de datos disponibles son:
            
            1. DBusuarios_app - Información de usuarios del sistema:
            {usuarios_schema}
            
            2. DBSistemaPOS - Sistema punto de venta:
            {pos_schema}
            
            IMPORTANTE: Determina cuál de las dos bases de datos debe usarse para la consulta.
            Si es DBusuarios_app, inicia tu respuesta con "BASE: USUARIOS" y luego la consulta SQL.
            Si es DBSistemaPOS, inicia tu respuesta con "BASE: POS" y luego la consulta SQL.
            
            Genera solo la consulta SQL con el prefijo de base de datos, sin explicaciones ni comentarios adicionales.
            """
            
            # Mensaje del usuario
            user_message = f"Convierte esta pregunta a SQL: {user_question}"
            
            # Generar la consulta SQL usando Replicate
            output = replicate.run(
                self.model,
                input={
                    "prompt": f"{system_prompt}\n\nUsuario: {user_message}\n\nAsistente:",
                    "temperature": 0.1,
                    "max_length": 500,
                    "repetition_penalty": 1.0
                }
            )
            
            # Construir la respuesta
            response = ""
            for item in output:
                response += item
            
            # Limpiar y extraer el prefijo de base de datos y la consulta SQL
            response = response.strip()
            
            # Extraer base de datos y consulta
            db_name = "usuarios"  # por defecto
            sql_query = response
            
            if response.upper().startswith("BASE: USUARIOS"):
                db_name = "usuarios"
                sql_query = response[14:].strip()  # Quitar "BASE: USUARIOS"
            elif response.upper().startswith("BASE: POS"):
                db_name = "pos"
                sql_query = response[10:].strip()  # Quitar "BASE: POS"
            
            # Verificar si la consulta es segura (evitar DELETE, DROP, UPDATE, etc.)
            unsafe_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
            if any(keyword in sql_query.upper() for keyword in unsafe_keywords):
                return "ERROR: La consulta no es segura para ejecutar. Solo se permiten consultas SELECT.", db_name
            
            # Asegurarse de que la consulta comienza con SELECT para seguridad
            if not sql_query.upper().startswith("SELECT"):
                return "ERROR: Solo se permiten consultas SELECT para seguridad.", db_name
                
            return sql_query, db_name
            
        except Exception as e:
            print(f"Error al generar la consulta SQL: {e}")
            return None, "usuarios"
    
    def answer_question(self, user_question):
        """Responder a la pregunta del usuario sobre la base de datos"""
        try:
            # Paso 1: Generar la consulta SQL y determinar la base de datos
            sql_query, db_name = self.generate_sql_query(user_question)
            
            if not sql_query or sql_query.startswith("ERROR"):
                return sql_query or "No pude generar una consulta SQL válida."
            
            # Paso 2: Ejecutar la consulta en la base de datos correcta
            results = self.execute_query(sql_query, db_name)
            
            if results is None:
                return "Hubo un error al ejecutar la consulta."
            
            # Paso 3: Formatear los resultados
            formatted_results = self.format_query_results(results)
            
            # Paso 4: Generar una respuesta en lenguaje natural usando Llama 3
            system_prompt = """
            Eres un asistente virtual para una empresa que explica datos de manera clara y concisa.
            Responde a la pregunta del usuario basándote en los resultados de consulta proporcionados.
            Sé útil y profesional.
            """
            
            user_message = f"""
            Pregunta: {user_question}
            
            Base de datos consultada: {db_configs[db_name]['database']}
            Consulta SQL ejecutada: {sql_query}
            
            Resultados:
            {formatted_results}
            
            Por favor, elabora una respuesta clara y concisa basada en estos resultados.
            """
            
            output = replicate.run(
                self.model,
                input={
                    "prompt": f"{system_prompt}\n\nUsuario: {user_message}\n\nAsistente:",
                    "temperature": 0.7,
                    "max_length": 1000,
                    "repetition_penalty": 1.0
                }
            )
            
            # Construir la respuesta
            response = ""
            for item in output:
                response += item
                
            return response
        except Exception as e:
            print(f"Error al responder la pregunta: {e}")
            return "Lo siento, no pude procesar tu pregunta en este momento. Por favor, intenta nuevamente más tarde." 