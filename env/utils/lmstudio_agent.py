import os
import mysql.connector
from mysql.connector import Error
import json
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class LMStudioAgent:
    def __init__(self, api_url="http://localhost:1234/v1"):
        """Inicializa el agente de LM Studio usando la API de OpenAI compatible."""
        self.api_url = api_url
        
        # Conexiones a bases de datos
        self.db_configs = {
            "usuarios": {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "dbusuarios_app"
            },
            "pos": {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "DBSistemaPOS"
            }
        }
    
    def get_db_schema(self, db_type):
        """Obtiene el esquema de la base de datos especificada."""
        schema_info = []
        
        try:
            # Conectar a la base de datos
            conn = mysql.connector.connect(**self.db_configs[db_type])
            cursor = conn.cursor()
            
            # Obtener lista de tablas
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            # Para cada tabla, obtener su estructura
            for table in tables:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                
                table_info = {
                    "table_name": table,
                    "columns": []
                }
                
                for column in columns:
                    table_info["columns"].append({
                        "name": column[0],
                        "type": column[1],
                        "null": column[2],
                        "key": column[3],
                        "default": column[4],
                        "extra": column[5]
                    })
                
                schema_info.append(table_info)
            
        except Error as e:
            print(f"Error al conectar a la base de datos {db_type}: {e}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
        return schema_info
    
    def execute_query(self, db_type, query):
        """Ejecuta una consulta SQL en la base de datos especificada."""
        results = []
        
        try:
            # Conectar a la base de datos
            conn = mysql.connector.connect(**self.db_configs[db_type])
            cursor = conn.cursor(dictionary=True)
            
            # Ejecutar consulta
            cursor.execute(query)
            results = cursor.fetchall()
            
        except Error as e:
            print(f"Error al ejecutar consulta en {db_type}: {e}")
            return {"error": str(e)}
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
        return results
    
    def generate_response(self, user_question):
        """Genera una respuesta utilizando LM Studio."""
        # Obtener esquemas de ambas bases de datos
        usuarios_schema = self.get_db_schema("usuarios")
        pos_schema = self.get_db_schema("pos")
        
        # Determinar qué base de datos se debe usar
        db_type = self.determine_db_type(user_question, usuarios_schema, pos_schema)
        
        # Crear el prompt para el modelo
        prompt = self.create_prompt(user_question, db_type, 
                                  usuarios_schema if db_type == "usuarios" else pos_schema)
        
        # Generar respuesta usando la API de LM Studio
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                json={
                    "model": "llama3",  # El modelo que esté cargado en LM Studio
                    "messages": [
                        {"role": "system", "content": "Eres un asistente experto en SQL que ayuda a generar consultas para una base de datos MySQL."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024
                }
            )
            
            if response.status_code != 200:
                return {
                    "response": f"Error al comunicarse con LM Studio: {response.text}",
                    "db_used": db_type,
                    "sql_query": None,
                    "data": None
                }
            
            response_data = response.json()
            answer = response_data["choices"][0]["message"]["content"]
            
            # Extraer la consulta SQL
            sql_query = self.extract_sql_query(answer)
            
            # Si hay una consulta SQL, ejecutarla
            data = None
            if sql_query:
                data = self.execute_query(db_type, sql_query)
            
            return {
                "response": answer.strip(),
                "db_used": db_type,
                "sql_query": sql_query,
                "data": data
            }
            
        except Exception as e:
            print(f"Error al generar respuesta: {e}")
            return {
                "response": f"Error al generar respuesta: {str(e)}",
                "db_used": db_type,
                "sql_query": None,
                "data": None
            }
    
    def determine_db_type(self, question, usuarios_schema, pos_schema):
        """Determina qué base de datos se debe usar basándose en la pregunta."""
        # Palabras clave para cada tipo de base de datos
        usuarios_keywords = ["usuario", "usuarios", "login", "contraseña", "acceso", "perfil", 
                            "admin", "administrador", "cargo", "email", "correo"]
        
        pos_keywords = ["venta", "ventas", "producto", "productos", "inventario", "stock", 
                       "precio", "caja", "factura", "pos", "punto de venta", "cliente", "proveedor"]
        
        # Contar coincidencias
        usuarios_count = sum(1 for kw in usuarios_keywords if kw.lower() in question.lower())
        pos_count = sum(1 for kw in pos_keywords if kw.lower() in question.lower())
        
        # Si hay tablas vacías en alguna BD, usar la otra
        if not usuarios_schema and pos_schema:
            return "pos"
        if not pos_schema and usuarios_schema:
            return "usuarios"
        
        # Decidir basándose en el conteo
        return "usuarios" if usuarios_count >= pos_count else "pos"
    
    def create_prompt(self, question, db_type, schema):
        """Crea un prompt para el modelo con la pregunta y el esquema de la base de datos."""
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
        
        prompt = f"""Base de datos: {self.db_configs[db_type]["database"]}
Esquema de la base de datos:
{schema_str}

Necesito que actúes como un experto en SQL. Basándote en el esquema de base de datos proporcionado, 
genera una consulta SQL que responda la siguiente pregunta: 

{question}

Por favor, primero explica brevemente cómo abordarás la consulta, luego proporciona la consulta SQL 
en formato de código, y finalmente explica cómo interpretar los resultados.
"""
        return prompt
    
    def extract_sql_query(self, text):
        """Extrae la consulta SQL de la respuesta generada."""
        # Buscar patrones comunes de consultas SQL
        sql_markers = [
            "```sql\n", "```mysql\n", "```\n",
            "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"
        ]
        
        for marker in sql_markers:
            if marker in text:
                # Si es un bloque de código, extraer entre los marcadores
                if marker.startswith("```"):
                    start_idx = text.find(marker) + len(marker)
                    end_idx = text.find("```", start_idx)
                    if end_idx != -1:
                        return text[start_idx:end_idx].strip()
                # Si es una palabra clave SQL, extraer hasta el final de línea o punto
                else:
                    idx = text.find(marker)
                    if idx != -1:
                        # Buscar el final de la consulta
                        for end_char in ["\n\n", ";\n", ";"]:
                            end_idx = text.find(end_char, idx)
                            if end_idx != -1:
                                return text[idx:end_idx + (1 if end_char == ";" else 0)].strip()
                        
                        # Si no se encontró un delimitador claro, tomar hasta el próximo párrafo
                        return text[idx:].split("\n\n")[0].strip()
        
        return None 