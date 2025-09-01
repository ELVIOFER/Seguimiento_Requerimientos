import os

# basedir calcula la ruta a la carpeta raíz del proyecto ('Seguimiento_Requerimientos')
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:
    """Clase de configuración base con valores comunes."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-llave-secreta-muy-dificil-de-adivinar'
    POSTS_PER_PAGE = 10
    
    # Esta opción de SQLAlchemy se recomienda ponerla en False.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """Configuración específica para el entorno de desarrollo."""
    DEBUG = True
    
    # La base de datos de desarrollo (tu "borrador").
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance/seguimiento_requerimientos_dev.sqlite')
    
    # La carpeta de uploads para desarrollo.
    UPLOAD_FOLDER = "uploads_dev"

class ProductionConfig(Config):
    """Configuración específica para el entorno de producción."""
    DEBUG = False
    
    # La base de datos "oficial".
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'instance/seguimiento_requerimientos.sqlite')

    # La carpeta de uploads para producción.
    UPLOAD_FOLDER = "uploads"

# Diccionario "selector" para elegir la configuración por nombre.
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig 
}