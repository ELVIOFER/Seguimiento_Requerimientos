# --- wsgi.py (Versión Final y Limpia) ---
import os
from src.app import create_app

# Lee la variable de entorno para saber qué configuración cargar
config_name = os.getenv('FLASK_ENV', 'default')

# Crea la aplicación usando la factoría
app = create_app(config_name)

# Este bloque permite ejecutar el archivo directamente con 'python wsgi.py'
if __name__ == "__main__":
    app.run()