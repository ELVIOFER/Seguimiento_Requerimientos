# --- src/database.py (Versión Final y Limpia con SQLAlchemy) ---

def get_or_create_provider(db_session, provider_model, provider_name):
    """
    Busca un proveedor por nombre usando SQLAlchemy. Si no existe, lo crea.
    Retorna la instancia del objeto Proveedor.
    
    Args:
        db_session: La sesión de SQLAlchemy (generalmente db.session).
        provider_model: La clase del modelo que se va a usar (la clase Proveedor).
        provider_name: El nombre del proveedor a buscar o crear.
    """
    provider_name = provider_name.strip()
    
    # 1. Hacemos la consulta usando el ORM de SQLAlchemy.
    #    .ilike() es para una búsqueda case-insensitive (ignora mayúsculas/minúsculas).
    proveedor = db_session.query(provider_model).filter(
        provider_model.nombre.ilike(provider_name)
    ).first()

    # 2. Si el proveedor existe, lo devolvemos.
    if proveedor:
        return proveedor
    else:
        # 3. Si no existe, creamos un nuevo objeto Proveedor.
        nuevo_proveedor = provider_model(nombre=provider_name)
        
        # 4. Lo añadimos a la "sesión" (como un área de preparación de cambios).
        db_session.add(nuevo_proveedor)
        
        # 5. Devolvemos el nuevo objeto. El 'commit' se hará en la ruta.
        return nuevo_proveedor