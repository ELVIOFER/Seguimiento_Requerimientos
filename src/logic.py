# --- src/logic.py (Simplificado después de la refactorización de fechas) ---

from datetime import datetime, timedelta, date
from .models import Requerimiento, Orden
from sqlalchemy import func
import os
import re
from flask import g, current_app, session
from werkzeug.utils import secure_filename

def parse_date_from_form(date_string):
    """
    Convierte una cadena de texto de un formulario ('YYYY-MM-DD')
    a un objeto date de Python. Retorna None si la cadena está vacía o es inválida.
    """
    if not date_string:
        return None
    try:
        # date.fromisoformat() es la forma moderna y eficiente de parsear 'YYYY-MM-DD'
        return date.fromisoformat(date_string)
    except (ValueError, TypeError):
        print(f"Advertencia: Formato de fecha inválido encontrado: '{date_string}'")
        return None

# LA FUNCIÓN 'procesar_item_requerimiento' HA SIDO ELIMINADA.
# La lógica de cálculo y formato ahora vive en las plantillas.

def calcular_estadisticas(db_session):
    """
    Calcula estadísticas clave de la base de datos usando SQLAlchemy.
    """
    total_requerimientos = db_session.query(func.count(Requerimiento.id)).scalar()
    total_ordenes = db_session.query(func.count(Orden.id)).scalar()
    monto_total = db_session.query(func.sum(Orden.monto)).scalar()
    
    estadisticas = {
        'total_requerimientos': total_requerimientos or 0,
        'total_ordenes': total_ordenes or 0,
        'monto_total': monto_total or 0.0
    }
    
    return estadisticas

def get_project_folder_name():
    """
    Genera un nombre de carpeta seguro a partir del nombre del proyecto actual.
    """
    if not g or not hasattr(g, 'tenant_id'):
        return None

    project_name = session.get('current_tenant_name', 'default-project')
    
    s = project_name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = s[:50]
    s = f"{s}_{g.tenant_id}"
    
    return s

def save_project_file(file_storage):
    """
    Guarda un archivo en la carpeta correcta del proyecto actual y
    devuelve la ruta relativa para guardar en la BD.
    """
    if not file_storage or file_storage.filename == '':
        return None

    filename = secure_filename(file_storage.filename)
    project_folder = get_project_folder_name()
    
    if not project_folder:
        raise Exception("No se puede guardar el archivo: No hay un proyecto seleccionado.")

    tenant_upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], project_folder)
    os.makedirs(tenant_upload_folder, exist_ok=True)
    
    file_storage.save(os.path.join(tenant_upload_folder, filename))
    
    return os.path.join(project_folder, filename)