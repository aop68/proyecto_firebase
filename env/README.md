# Dashboard Empresarial con Agente de Base de Datos

## Descripción
Aplicación web Flask que proporciona un dashboard empresarial completo con visualizaciones de datos en tiempo real, análisis descriptivo, datos globales y análisis predictivo. Incluye un agente de IA basado en LLama para consultas a la base de datos mediante lenguaje natural.

## Características
- **Dashboard multifuncional**: Visualizaciones de datos en tiempo real, descriptivas, globales y predictivas.
- **Agente de IA**: Permite realizar consultas en lenguaje natural a la base de datos.
- **Sistema de usuarios**: Gestión de usuarios con diferentes niveles de acceso.
- **Interfaz responsive**: Diseñada para funcionar en cualquier dispositivo.

## Tecnologías utilizadas
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Base de datos**: MySQL
- **Visualizaciones**: Power BI embebido
- **IA**: Modelo Llama 3 mediante LM Studio

## Instalación

1. Clonar el repositorio:
```
git clone [URL del repositorio]
cd [nombre del directorio]
```

2. Crear y activar entorno virtual:
```
python -m venv env
env\Scripts\activate
```

3. Instalar dependencias:
```
pip install -r requirements.txt
```

4. Configurar la base de datos:
- Crear una base de datos MySQL
- Actualizar la configuración en el archivo `app.py`

5. Ejecutar la aplicación:
```
python app.py
```

## Uso
- Accede a la aplicación en http://localhost:80
- Inicia sesión con las credenciales predeterminadas:
  - Usuario: admin@empresa.com
  - Contraseña: admin123

## Licencia
Este proyecto está bajo licencia MIT. 