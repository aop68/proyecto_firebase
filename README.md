# Agente Inteligente con Llama 3

Este proyecto implementa un agente inteligente basado en el modelo Llama 3 que puede interactuar con bases de datos MySQL para responder preguntas en lenguaje natural.

## Características

- Integración con el modelo Llama 3 a través de LM Studio
- Conexión a múltiples bases de datos MySQL
- Interfaz web amigable para interactuar con el agente
- Generación de consultas SQL basadas en preguntas en lenguaje natural
- Visualización de resultados en formato tabular

## Requisitos

- Python 3.11 o superior
- MySQL Server
- LM Studio con el modelo Llama 3 70B Instruct
- Las siguientes bases de datos:
  - DBusuarios_app
  - DBSistemaPOS

## Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd [NOMBRE_DEL_REPOSITORIO]
```

2. Crear y activar un entorno virtual:
```bash
python -m venv env
.\env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar el archivo .env:
```bash
cp .env.example .env
# Editar .env con tus credenciales de MySQL
```

## Uso

1. Iniciar LM Studio y cargar el modelo Llama 3 70B Instruct
2. Iniciar el servidor local en LM Studio (puerto 1234)
3. Ejecutar la aplicación:
```bash
python app.py
```
4. Abrir el navegador en http://localhost:5000

## Estructura del Proyecto

```
.
├── app.py              # Aplicación principal Flask
├── requirements.txt    # Dependencias del proyecto
├── templates/          # Plantillas HTML
│   └── agente.html    # Interfaz del agente
└── utils/             # Utilidades
    └── lmstudio_agent.py  # Agente de LM Studio
```

## Ejemplos de Preguntas

- "¿Cuántos usuarios hay en total?"
- "¿Cuál es el producto más vendido?"
- "¿Cuántas ventas se realizaron hoy?"
- "¿Quiénes son los administradores del sistema?"

## Licencia

Este proyecto está bajo la Licencia MIT. 