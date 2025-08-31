# --- Archivo: app.py (Versión final con todas las correcciones y mejoras) ---

import sqlite3
import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    abort,
    flash,
)
from werkzeug.utils import secure_filename
from .database import get_db, init_app, get_or_create_provider
from .logic import procesar_item_requerimiento
from .routes import requerimiento
from .routes import requerimiento, orden  

app = Flask(__name__)

# --- Configuraciones (sin cambios) ---
app.config["DATABASE"] = "instance/control_proyectos.sqlite"
os.makedirs(app.instance_path, exist_ok=True)
app.config["SECRET_KEY"] = "tu-clave-secreta-aqui-cambiar-en-produccion"
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.config["POSTS_PER_PAGE"] = 10

# --- Inicialización (sin cambios) ---
init_app(app)
app.register_blueprint(requerimiento.bp)
app.register_blueprint(orden.bp)

# --- Rutas Principales (sin cambios) ---
@app.route("/")
def index():
    # ... (código sin cambios)
    page = request.args.get("page", 1, type=int)
    query_search = request.args.get("q")
    sort_by = request.args.get("sort_by", "fecha_presentacion")
    order = request.args.get("order", "desc")
    allowed_sort_columns = {
        "numero_requerimiento": "r.numero_requerimiento",
        "fecha_presentacion": "r.fecha_presentacion",
        "estado": "r.estado",
    }
    sort_column = allowed_sort_columns.get(sort_by, "r.fecha_presentacion")
    if order not in ["asc", "desc"]:
        order = "desc"
    db = get_db()
    params = []
    count_query = "SELECT COUNT(r.id) FROM requerimiento r"
    if query_search:
        count_query += " WHERE r.numero_requerimiento LIKE ? OR r.descripcion LIKE ?"
        params.extend([f"%{query_search}%", f"%{query_search}%"])
    total_items = db.execute(count_query, params).fetchone()[0]
    offset = (page - 1) * app.config["POSTS_PER_PAGE"]
    base_query = (
        "SELECT r.id, r.numero_requerimiento, r.descripcion, "
        "r.fecha_presentacion, r.estado, r.archivo_path, "
        "o.id as orden_id, o.fecha_emision, o.fecha_notificacion, "
        "o.monto, o.plazo_ejecucion_dias, p.nombre as proveedor_nombre "
        "FROM requerimiento r "
        "LEFT JOIN orden o ON r.id = o.requerimiento_id "
        "LEFT JOIN proveedor p ON o.proveedor_id = p.id"
    )
    if query_search:
        base_query += " WHERE r.numero_requerimiento LIKE ? OR r.descripcion LIKE ?"
    base_query += f" ORDER BY {sort_column} {order.upper()} LIMIT ? OFFSET ?;"
    params.extend([app.config["POSTS_PER_PAGE"], offset])
    items = db.execute(base_query, params).fetchall()
    resultados_procesados = [procesar_item_requerimiento(item) for item in items]
    return render_template(
        "index.html",
        resultados=resultados_procesados,
        page=page,
        total_items=total_items,
        per_page=app.config["POSTS_PER_PAGE"],
        query_search=query_search,
        sort_by=sort_by,
        order=order,
    )


@app.route("/uploads/<path:filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
