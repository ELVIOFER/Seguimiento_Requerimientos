from datetime import datetime, timedelta

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

    # Lógica para 'dias_hasta_notificacion'
    if fecha_presentacion and fecha_notificacion:
        item_procesado["dias_hasta_notificacion"] = (
            fecha_notificacion - fecha_presentacion
        ).days

    # Lógica para 'fecha_culminacion'
    plazo_dias = item_procesado.get("plazo_ejecucion_dias")
    if fecha_notificacion and isinstance(plazo_dias, int):
        plazo = timedelta(days=plazo_dias)
        fecha_culminacion_obj = fecha_notificacion + plazo
        item_procesado["fecha_culminacion"] = fecha_culminacion_obj.strftime("%Y-%m-%d")

    return item_procesado