import sys
import os

# Agregar el directorio de la aplicación al path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Importar la aplicación
from app import app as application 