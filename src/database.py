import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

# <<<--- AQUÍ ES DONDE PEGAMOS LA FUNCIÓN --- >>>
def get_or_create_provider(db, provider_name):
    """
    Busca un proveedor por nombre. Si no existe, lo crea.
    Retorna el ID del proveedor.
    """
    provider_name = provider_name.strip()
    proveedor = db.execute(
        "SELECT id FROM proveedor WHERE LOWER(nombre) = LOWER(?)", (provider_name,)
    ).fetchone()
    if proveedor:
        return proveedor["id"]
    else:
        cursor = db.execute(
            "INSERT INTO proveedor (nombre) VALUES (?)", (provider_name,)
        )
        return cursor.lastrowid

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))

@click.command("init-db")
@with_appcontext  # <- Tu decorador está correctamente aquí
def init_db_command():
    """Limpia los datos existentes y crea las tablas nuevas."""
    init_db()
    click.echo("Base de datos inicializada.")

def init_app(app):
    """Registra funciones de base de datos con la aplicación Flask."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)