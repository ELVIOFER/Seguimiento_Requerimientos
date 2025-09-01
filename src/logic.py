# --- src/logic.py (Versión Corregida) ---

from datetime import datetime, timedelta
# Importamos los modelos para poder hacer consultas en la nueva función
from .models import Requerimiento, Orden
# Importamos 'func' de SQLAlchemy para usar funciones como COUNT y SUM
from sqlalchemy import func

def parsear_fecha(fecha_str):
    """
    Convierte una cadena de texto en formato 'YYYY-MM-DD' a un objeto datetime.
    Retorna None si la cadena es nula, está vacía o tiene un formato incorrecto.
    """
    if not fecha_str:
        return None
    try:
        # Intenta convertir la cadena a un objeto de fecha
        return datetime.strptime(fecha_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        # Si el formato es incorrecto o no es una cadena, devuelve None
        print(f"Advertencia: Formato de fecha inválido encontrado: '{fecha_str}'")
        return None


def procesar_item_requerimiento(item):
    """
    Toma un diccionario de requerimiento (de la BD) y calcula los campos derivados.
    """
    item_procesado = dict(item)
    item_procesado["dias_hasta_emision"] = None
    item_procesado["dias_hasta_notificacion"] = None
    item_procesado["fecha_culminacion"] = None

    # Usamos nuestra función de parseo segura
    fecha_presentacion = parsear_fecha(item_procesado.get("fecha_presentacion"))
    fecha_notificacion = parsear_fecha(item_procesado.get("fecha_notificacion"))
    # Añadimos el parseo de la fecha de emisión
    fecha_emision = parsear_fecha(item_procesado.get("fecha_emision"))

    # =========================================================================
    # <<< --- ESTA ES LA LÓGICA DE CÁLCULO QUE HEMOS AÑADIDO --- >>>
    if fecha_presentacion and fecha_emision:
        diferencia = fecha_emision - fecha_presentacion
        item_procesado["dias_hasta_emision"] = diferencia.days
    # =========================================================================

    # Lógica para 'dias_hasta_notificacion' (sin cambios)
    if fecha_presentacion and fecha_notificacion:
        item_procesado["dias_hasta_notificacion"] = (
            fecha_notificacion - fecha_presentacion
        ).days

    # Lógica para 'fecha_culminacion' (sin cambios)
    plazo_dias = item_procesado.get("plazo_ejecucion_dias")
    if fecha_notificacion and isinstance(plazo_dias, int):
        plazo = timedelta(days=plazo_dias)
        fecha_culminacion_obj = fecha_notificacion + plazo
        item_procesado["fecha_culminacion"] = fecha_culminacion_obj.strftime("%Y-%m-%d")

    return item_procesado


def calcular_estadisticas(db_session):
    """
    Calcula estadísticas clave de la base de datos usando SQLAlchemy.
    
    Args:
        db_session: La sesión activa de la base de datos (db.session).
        
    Returns:
        Un diccionario con las estadísticas calculadas.
    """
    # Consulta para contar el total de requerimientos
    total_requerimientos = db_session.query(func.count(Requerimiento.id)).scalar()
    
    # Consulta para contar el total de órdenes
    total_ordenes = db_session.query(func.count(Orden.id)).scalar()
    
    # Consulta para sumar el monto de todas las órdenes
    monto_total = db_session.query(func.sum(Orden.monto)).scalar()
    
    # Creamos el diccionario de resultados, asegurándonos de que no haya Nones
    estadisticas = {
        'total_requerimientos': total_requerimientos or 0,
        'total_ordenes': total_ordenes or 0,
        'monto_total': monto_total or 0.0
    }
    
    return estadisticas