from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from utils.lmstudio_agent import LMStudioAgent
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Cambia esto por una clave secreta segura

# Configuración de la base de datos
db_config = {
    'host': 'trolley.proxy.rlwy.net',
    'port': 37649,
    'user': 'root',
    'password': 'ivPrQpJMsVQQVgoHMqvrZwGkmfoBxjjQ',
    'database': 'DBusuarios_app'
}

# Inicializar el agente LM Studio
agent = LMStudioAgent()

# Configuración de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Clase de usuario para Flask-Login
class User(UserMixin):
    def __init__(self, id, nombre, email, cargo, imagen=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.cargo = cargo
        self.imagen = imagen

# Función para conectar a la base de datos
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

# Función para crear la tabla de usuarios si no existe
def create_users_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SHOW TABLES LIKE 'usuarios'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Verificar la estructura de la tabla
            cursor.execute("DESCRIBE usuarios")
            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]
            print(f"Estructura actual de la tabla: {column_names}")
            
            # Si no tiene la estructura correcta, recrearla
            required_columns = ['id', 'nombre', 'email', 'password', 'cargo', 'imagen']
            missing_columns = [col for col in required_columns if col not in column_names]
            
            if missing_columns:
                print(f"Faltan columnas: {missing_columns}. Recreando la tabla...")
                cursor.execute("DROP TABLE usuarios")
                # Recrear la tabla con la estructura correcta
                cursor.execute('''
                    CREATE TABLE usuarios (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        nombre VARCHAR(100) NOT NULL,
                        email VARCHAR(100) NOT NULL UNIQUE,
                        password VARCHAR(255) NOT NULL,
                        cargo VARCHAR(50) NOT NULL,
                        imagen VARCHAR(255)
                    )
                ''')
                print("Tabla recreada correctamente")
        else:
            # Crear tabla de usuarios con la estructura correcta
            cursor.execute('''
                CREATE TABLE usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    cargo VARCHAR(50) NOT NULL,
                    imagen VARCHAR(255)
                )
            ''')
            print("Tabla usuarios creada correctamente")
        
        # Verificar si ya existe un administrador
        try:
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE cargo = 'administrador'")
            admin_count = cursor.fetchone()[0]
            
            # Si no hay administrador, crear uno por defecto
            if admin_count == 0:
                hashed_password = generate_password_hash('admin123')
                cursor.execute('''
                    INSERT INTO usuarios (nombre, email, password, cargo)
                    VALUES (%s, %s, %s, %s)
                ''', ('Administrador', 'admin@empresa.com', hashed_password, 'administrador'))
                print("Usuario administrador creado correctamente")
        except mysql.connector.Error as err:
            print(f"Error al verificar o crear administrador: {err}")
        
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error al crear la tabla de usuarios: {err}")

# Crear tabla de usuarios al iniciar la aplicación
create_users_table()

# Callback para cargar un usuario
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user_data:
        return User(
            id=user_data['id'],
            nombre=user_data['nombre'],
            email=user_data['email'],
            cargo=user_data['cargo'],
            imagen=user_data['imagen']
        )
    return None

# Ruta de inicio
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data and check_password_hash(user_data['password'], password):
            user = User(
                id=user_data['id'],
                nombre=user_data['nombre'],
                email=user_data['email'],
                cargo=user_data['cargo'],
                imagen=user_data['imagen']
            )
            login_user(user)
            session['user_id'] = user_data['id']
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas. Intente nuevamente.', 'error')
    
    return render_template('login.html')

# Ruta de cierre de sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Ruta del dashboard principal
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', active='tiempo_real')

# Rutas para las diferentes vistas del dashboard
@app.route('/dashboard/tiempo_real')
@login_required
def tiempo_real():
    return render_template('dashboard.html', active='tiempo_real')

@app.route('/dashboard/descriptiva')
@login_required
def descriptiva():
    return render_template('dashboard.html', active='descriptiva')

@app.route('/dashboard/cuota_mercado')
@login_required
def cuota_mercado():
    return render_template('dashboard.html', active='cuota_mercado')

@app.route('/dashboard/predictiva')
@login_required
def predictiva():
    return render_template('dashboard.html', active='predictiva')

# Ruta para el agente LLM
@app.route('/agente')
@login_required
def agente():
    return render_template('agente.html')

# API para procesar preguntas a través del agente
@app.route('/api/agent/ask', methods=['POST'])
@login_required
def agent_ask():
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({'error': 'No se proporcionó ninguna pregunta'}), 400
    
    question = data['question']
    
    # Usar el agente Llama 3 local para responder
    response = agent.generate_response(question)
    
    return jsonify({
        'response': response.get('response', ''),
        'db_used': response.get('db_used', ''),
        'sql_query': response.get('sql_query', ''),
        'data': response.get('data', []),
        'success': True
    })

# Ruta para la gestión de equipo
@app.route('/equipo')
@login_required
def equipo():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('equipo.html', usuarios=usuarios)

# Ruta para agregar usuario
@app.route('/equipo/agregar', methods=['GET', 'POST'])
@login_required
def agregar_usuario():
    if current_user.cargo != 'administrador':
        flash('No tiene permisos para realizar esta acción', 'error')
        return redirect(url_for('equipo'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        cargo = request.form['cargo']
        
        imagen = None
        if 'imagen' in request.files and request.files['imagen'].filename:
            file = request.files['imagen']
            filename = secure_filename(file.filename)
            file_path = os.path.join('static/images', filename)
            file.save(file_path)
            imagen = file_path
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO usuarios (nombre, email, password, cargo, imagen)
                VALUES (%s, %s, %s, %s, %s)
            ''', (nombre, email, hashed_password, cargo, imagen))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Usuario agregado correctamente', 'success')
            return redirect(url_for('equipo'))
        except mysql.connector.Error as err:
            flash(f'Error al agregar usuario: {err}', 'error')
    
    return render_template('agregar_usuario.html')

# Ruta para editar usuario
@app.route('/equipo/editar/<int:user_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(user_id):
    if current_user.cargo != 'administrador' and current_user.id != user_id:
        flash('No tiene permisos para realizar esta acción', 'error')
        return redirect(url_for('equipo'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('equipo'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        cargo = request.form['cargo']
        
        # Si es administrador, puede cambiar el cargo, si no, mantiene el cargo original
        if current_user.cargo != 'administrador':
            cargo = usuario['cargo']
        
        # Mantener la imagen original si no se proporciona una nueva
        imagen = usuario['imagen']
        if 'imagen' in request.files and request.files['imagen'].filename:
            file = request.files['imagen']
            filename = secure_filename(file.filename)
            file_path = os.path.join('static/images', filename)
            file.save(file_path)
            imagen = file_path
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Si se proporciona una nueva contraseña, actualizarla
            if request.form.get('password'):
                hashed_password = generate_password_hash(request.form['password'])
                cursor.execute('''
                    UPDATE usuarios 
                    SET nombre = %s, email = %s, password = %s, cargo = %s, imagen = %s
                    WHERE id = %s
                ''', (nombre, email, hashed_password, cargo, imagen, user_id))
            else:
                cursor.execute('''
                    UPDATE usuarios 
                    SET nombre = %s, email = %s, cargo = %s, imagen = %s
                    WHERE id = %s
                ''', (nombre, email, cargo, imagen, user_id))
                
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Usuario actualizado correctamente', 'success')
            return redirect(url_for('equipo'))
        except mysql.connector.Error as err:
            flash(f'Error al actualizar usuario: {err}', 'error')
    
    return render_template('editar_usuario.html', usuario=usuario)

# Modificar la ruta de las imágenes para que funcione en PythonAnywhere
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if __name__ == '__main__':
    # En desarrollo, usar puerto 80 para acceso web estándar
    app.run(host='0.0.0.0', port=80, debug=True)
else:
    # En producción (PythonAnywhere)
    application = app 