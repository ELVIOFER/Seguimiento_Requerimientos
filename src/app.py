# --- Archivo: app.py (Versión Final con Comando reset-db) ---

import os
import datetime
import click
from flask import (
    Flask, render_template, request, send_from_directory
)
from flask_migrate import Migrate, upgrade

# 1. Importamos nuestras propias partes de la aplicación
from .config import config_by_name
from .models import db, Requerimiento, Orden, Proveedor
from .logic import procesar_item_requerimiento

# 2. Inicializamos las extensiones fuera de la factoría
migrate = Migrate()

def create_app(config_name):
    """
    Función de factoría que crea y configura la instancia de la aplicación Flask.
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # 3. Cargar la configuración
    app.config.from_object(config_by_name[config_name])
    
    # Puedes eliminar esta línea de print si quieres, ya ha cumplido su misión de depuración
    print(f"--- MODO: {config_name}, BASE DE DATOS: {app.config['SQLALCHEMY_DATABASE_URI']} ---")

    # 4. Asegurarse de que las carpetas necesarias existan
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.makedirs(os.path.join(project_root, app.config["UPLOAD_FOLDER"]), exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # 5. Inicializar las extensiones
    db.init_app(app)
    migrate.init_app(app, db)

    # 6. Registrar los Blueprints
    from .routes import requerimiento, orden
    app.register_blueprint(requerimiento.bp)
    app.register_blueprint(orden.bp)
    
    # 7. Registrar el procesador de contexto, rutas y comandos CLI
    with app.app_context():
        
        @app.context_processor
        def inject_now():
            return {'now': datetime.datetime.utcnow}

        # --- Rutas Principales ---
        @app.route("/")
        def index():
            # ... (código de la ruta index sin cambios)
            page = request.args.get("page", 1, type=int)
            query_search = request.args.get("q")
            sort_by = request.args.get("sort_by", "fecha_presentacion")
            order = request.args.get("order", "desc")
            query = db.session.query(Requerimiento, Orden, Proveedor).outerjoin(Orden, Requerimiento.id == Orden.requerimiento_id).outerjoin(Proveedor, Orden.proveedor_id == Proveedor.id)
            if query_search:
                search_term = f"%{query_search}%"
                query = query.filter(db.or_(Requerimiento.numero_requerimiento.like(search_term), Requerimiento.descripcion.like(search_term)))
            sort_map = {"numero_requerimiento": Requerimiento.numero_requerimiento, "fecha_presentacion": Requerimiento.fecha_presentacion, "estado": Requerimiento.estado}
            sort_column = sort_map.get(sort_by, Requerimiento.fecha_presentacion)
            if order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            pagination = query.paginate(page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
            items = pagination.items
            resultados_procesados = []
            for req, orden, prov in items:
                item_dict = {'id': req.id, 'numero_requerimiento': req.numero_requerimiento, 'descripcion': req.descripcion, 'fecha_presentacion': req.fecha_presentacion, 'estado': req.estado, 'archivo_path': req.archivo_path, 'orden_id': orden.id if orden else None, 'fecha_emision': orden.fecha_emision if orden else None, 'fecha_notificacion': orden.fecha_notificacion if orden else None, 'monto': orden.monto if orden else None, 'plazo_ejecucion_dias': orden.plazo_ejecucion_dias if orden else None, 'proveedor_nombre': prov.nombre if prov else None}
                resultados_procesados.append(procesar_item_requerimiento(item_dict))
            return render_template("index.html", resultados=resultados_procesados, pagination=pagination, query_search=query_search, sort_by=sort_by, order=order)

        @app.route("/uploads/<path:filename>")
        def download_file(filename):
            return send_from_directory(os.path.join(project_root, app.config["UPLOAD_FOLDER"]), filename)
        
        # <<< --- AQUÍ ESTÁ EL NUEVO COMANDO --- >>>
        @app.cli.command("reset-db")
        def reset_db_command():
            """Borra y recrea la base de datos desde las migraciones."""
            
            db_path_str = app.config.get('SQLALCHEMY_DATABASE_URI')
            if db_path_str and db_path_str.startswith('sqlite:///'):
                # Extraemos la ruta del archivo de la URI
                db_path = db_path_str.split('sqlite:///', 1)[1]
                
                # SQLite crea la ruta relativa al directorio 'instance', así que la construimos
                if not os.path.isabs(db_path):
                     db_path = os.path.join(app.instance_path, db_path)

                if os.path.exists(db_path):
                    os.remove(db_path)
                    click.echo(f"Base de datos eliminada: {db_path}")

            # Ejecutar 'db upgrade' para crear la base de datos y las tablas
            upgrade()
            click.echo("Base de datos reiniciada con éxito.")
            
    return app