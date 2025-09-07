# Contenido para wsgi.py

import os
from src.app import create_app

# Aquí está la magia: le decimos a Flask que use la configuración 'development'
# a menos que una variable de entorno FLASK_ENV diga lo contrario.
# Esto hace que 'development' sea nuestro modo de trabajo por defecto.
config_name = os.getenv('FLASK_ENV') or 'development'

# Creamos la aplicación usando esa configuración.
app = create_app(config_name)

# Esto es útil si quieres ejecutar directamente con `python wsgi.py`
if __name__ == "__main__":
    app.run()