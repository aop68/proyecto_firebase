import os
import mysql.connector
from mysql.connector import Error
from llama_cpp import Llama
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class LocalLlamaAgent:
    def __init__(self):
        # Ruta al modelo local (debe ser descargado previamente)
        self.model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "llama-3-8b-instruct.Q4_K_M.gguf")
        
        # Inicializar modelo (solo si existe)
        self.model = None
        if os.path.exists(self.model_path):
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=4096,           # Tamaño de contexto
                n_gpu_layers=-1,      # Utilizar GPU si está disponible (-1 = auto)
                verbose=False
            )
        
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
    
    def download_model_if_needed(self):
        """Descarga el modelo si no existe localmente."""
        if not os.path.exists(self.model_path):
            models_dir = os.path.dirname(self.model_path)
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)
            
            print("Descargando modelo Llama 3 (esto puede tardar varios minutos)...")
            
            from huggingface_hub import hf_hub_download
            
            # Descargar modelo desde Hugging Face
            try:
                hf_hub_download(
                    repo_id="TheBloke/Llama-3-8B-Instruct-GGUF",
                    filename="llama-3-8b-instruct.Q4_K_M.gguf",
                    local_dir=models_dir,
                    local_dir_use_symlinks=False
                )
                
                # Inicializar modelo después de descargar
                self.model = Llama(
                    model_path=self.model_path,
                    n_ctx=4096,
                    n_gpu_layers=-1,
                    verbose=False
                )
                print("Modelo descargado e inicializado correctamente")
                
            except Exception as e:
                print(f"Error al descargar el modelo: {e}")
                return False
            
            return True
        return True
    
    def generate_response(self, user_question):
        """Genera una respuesta utilizando el modelo local de Llama 3."""
        if self.model is None:
            success = self.download_model_if_needed()
            if not success:
                return {
                    "response": "No se pudo cargar el modelo local. Por favor, descarga el modelo manualmente.",
                    "db_used": None,
                    "sql_query": None,
                    "data": None
                }
        
        # Obtener esquemas de ambas bases de datos
        usuarios_schema = self.get_db_schema("usuarios")
        pos_schema = self.get_db_schema("pos")
        
        # Determinar qué base de datos se debe usar (análisis simple basado en palabras clave)
        db_type = self.determine_db_type(user_question, usuarios_schema, pos_schema)
        
        # Crear el prompt para el modelo
        prompt = self.create_prompt(user_question, db_type, 
                                   usuarios_schema if db_type == "usuarios" else pos_schema)
        
        # Generar respuesta
        try:
            output = self.model.create_completion(
                prompt,
                max_tokens=1024,
                temperature=0.1,
                top_p=0.9,
                stop=["</answer>", "\n\n"]
            )
            
            # Extraer la respuesta y la consulta SQL
            answer = output["choices"][0]["text"]
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
        
        prompt = f"""<s>
Eres un asistente experto en SQL que ayuda a generar consultas para una base de datos MySQL.
Tu tarea es generar una consulta SQL que responda a la pregunta del usuario, basándote en el esquema proporcionado.
Luego, explica los resultados de manera clara y concisa.
</s>

<user>
Base de datos: {self.db_configs[db_type]["database"]}
Esquema de la base de datos:
{schema_str}

Mi pregunta es: {question}
</user>

<assistant>
Basándome en tu pregunta, voy a generar una consulta SQL adecuada.
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