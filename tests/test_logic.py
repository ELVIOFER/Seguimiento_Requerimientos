# --- tests/test_logic.py (CONTENIDO FINAL) ---

import datetime
# Importamos la función que queremos probar desde su ubicación en 'src'
from src.logic import parsear_fecha

def test_parsear_fecha_con_cadena_valida():
    """Prueba que una cadena de fecha correcta se convierte bien."""
    
    # 1. Preparación de los datos (Arrange)
    fecha_en_texto = "2025-08-31"
    
    # 2. Ejecución de la función (Act)
    resultado = parsear_fecha(fecha_en_texto)
    
    # 3. Verificación de los resultados (Assert)
    # Afirmamos que el resultado es un objeto datetime
    assert isinstance(resultado, datetime.datetime)
    # Afirmamos que los componentes de la fecha son correctos
    assert resultado.year == 2025
    assert resultado.month == 8
    assert resultado.day == 31

def test_parsear_fecha_con_formato_invalido():
    """Prueba que una cadena con mal formato devuelve None."""
    resultado = parsear_fecha("31-08-2025") # Formato DD-MM-YYYY, incorrecto
    assert resultado is None

def test_parsear_fecha_con_texto_basura():
    """Prueba que una cadena que no es una fecha devuelve None."""
    resultado = parsear_fecha("hola mundo")
    assert resultado is None

def test_parsear_fecha_con_entrada_nula():
    """Prueba que si no se le pasa nada (None), devuelve None."""
    resultado = parsear_fecha(None)
    assert resultado is None

def test_parsear_fecha_con_cadena_vacia():
    """Prueba que una cadena vacía devuelve None."""
    resultado = parsear_fecha("")
    assert resultado is None