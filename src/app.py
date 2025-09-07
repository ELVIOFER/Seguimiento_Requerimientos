# --- Archivo: src/app.py (Refactorizado con Lógica de Carpetas Centralizada) ---

import os
import datetime
from datetime import timedelta
import click
import shutil
import re
from flask import (
    Flask, render_template, request, send_from_directory, g, redirect, url_for, session, flash, abort
)
from flask_migrate import Migrate, upgrade
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from .models import db, Requerimiento, Orden, Proveedor, Tenant
from .forms import TenantForm
from .config import config_by_name
# Importamos nuestra función de ayuda centralizada
from .logic import parse_date_from_form, get_project_folder_name

migrate = Migrate()

def create_app(config_name):
    """
    Función de factoría que crea y configura la instancia de la aplicación Flask.
    """
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_object(config_by_name[config_name])
    
    if not app.config.get('SECRET_KEY'):
        raise ValueError("No se ha configurado una SECRET_KEY. La sesión no funcionará.")

    print(f"--- MODO: {config_name}, BASE DE DATOS: {app.config['SQLALCHEMY_DATABASE_URI']} ---")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.makedirs(os.path.join(project_root, app.config["UPLOAD_FOLDER"]), exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    # Registro de Blueprints
    from .routes import requerimiento, orden, documento
    app.register_blueprint(requerimiento.bp)
    app.register_blueprint(orden.bp)
    app.register_blueprint(documento.bp)
    
    with app.app_context():
        
        @app.context_processor
        def inject_utilities():
            return dict(
                now=datetime.datetime.utcnow,
                current_tenant_name=session.get('current_tenant_name'),
                timedelta=timedelta
            )

        @app.before_request
        def set_current_tenant_from_session():
            tenant_id = session.get('current_tenant_id')
            endpoint = request.endpoint.split('.')[0] if '.' in (request.endpoint or '') else request.endpoint
            allowed_endpoints = ['select_tenant', 'set_tenant', 'create_tenant', 'edit_tenant', 'delete_tenant', 'static']
            if tenant_id:
                g.tenant_id = tenant_id
            elif endpoint not in allowed_endpoints:
                return redirect(url_for('select_tenant'))

        # --- Rutas Principales (Fuera de Blueprints) ---

        @app.route("/")
        def index():
            if 'current_tenant_id' not in session:
                return redirect(url_for('select_tenant'))
            
            page = request.args.get("page", 1, type=int)
            query_search = request.args.get("q")
            sort_by = request.args.get("sort_by", "fecha_presentacion")
            order = request.args.get("order", "desc")
            
            query = Requerimiento.query.options(db.joinedload(Requerimiento.orden).joinedload(Orden.proveedor))
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
            
            return render_template("index.html", 
                                   pagination=pagination, 
                                   query_search=query_search, 
                                   sort_by=sort_by, 
                                   order=order)
        
        @app.route("/select-project")
        def select_tenant():
            all_tenants = db.session.query(Tenant).order_by(Tenant.created_at.desc()).all()
            return render_template("select_tenant.html", tenants=all_tenants, title="Seleccionar Proyecto")

        @app.route("/set-project/<int:tenant_id>")
        def set_tenant(tenant_id):
            tenant = Tenant.query.get(tenant_id)
            if tenant:
                session['current_tenant_id'] = tenant.id
                session['current_tenant_name'] = tenant.name
            return redirect(url_for('index'))
        
        @app.route("/create-project", methods=['GET', 'POST'])
        def create_tenant():
            form = TenantForm()
            if form.validate_on_submit():
                new_tenant = Tenant(name=form.name.data.strip())
                db.session.add(new_tenant)
                try:
                    db.session.commit()
                    flash(f'Proyecto "{new_tenant.name}" creado con éxito.', 'success')
                    return redirect(url_for('select_tenant'))
                except IntegrityError:
                    db.session.rollback()
                    flash(f'Ya existe un proyecto con el nombre "{new_tenant.name}". Por favor, elige otro.', 'warning')
            return render_template('create_tenant.html', title='Crear Nuevo Proyecto', form=form)

        @app.route("/edit-project/<int:tenant_id>", methods=['GET', 'POST'])
        def edit_tenant(tenant_id):
            tenant = db.session.get(Tenant, tenant_id)
            if not tenant:
                abort(404)
            
            old_folder_name = get_project_folder_name(tenant)
            old_folder_path = os.path.join(project_root, app.config["UPLOAD_FOLDER"], old_folder_name) if old_folder_name else None
            
            form = TenantForm(obj=tenant)
            if form.validate_on_submit():
                new_name = form.name.data.strip()
                existing_tenant = db.session.query(Tenant).filter(Tenant.name == new_name, Tenant.id != tenant_id).first()

                if existing_tenant:
                    flash(f'El nombre "{new_name}" ya está en uso por otro proyecto.', 'warning')
                else:
                    tenant.name = new_name
                    db.session.commit()
                    
                    new_folder_name = get_project_folder_name(tenant)
                    new_folder_path = os.path.join(project_root, app.config["UPLOAD_FOLDER"], new_folder_name) if new_folder_name else None
                    
                    if old_folder_path and new_folder_path and os.path.exists(old_folder_path) and old_folder_path != new_folder_path:
                        try:
                            os.rename(old_folder_path, new_folder_path)
                            flash('El nombre del proyecto y su carpeta de archivos se han actualizado.', 'success')
                        except OSError as e:
                            flash(f'El nombre del proyecto se actualizó, pero hubo un error al renombrar la carpeta: {e}', 'danger')
                    else:
                        flash(f'El nombre del proyecto se ha actualizado a "{new_name}".', 'success')
                    
                    return redirect(url_for('select_tenant'))
            
            return render_template('edit_project.html', form=form, tenant=tenant)

        @app.route("/delete-project/<int:tenant_id>", methods=['POST'])
        def delete_tenant(tenant_id):
            tenant = db.session.get(Tenant, tenant_id)
            if not tenant:
                abort(404)
            try:
                project_folder_name = get_project_folder_name(tenant)
                if project_folder_name:
                    folder_to_delete = os.path.join(project_root, app.config["UPLOAD_FOLDER"], project_folder_name)
                    if os.path.exists(folder_to_delete):
                        shutil.rmtree(folder_to_delete)

                db.session.delete(tenant)
                db.session.commit()
                flash(f'El proyecto "{tenant.name}" y todo su contenido han sido eliminados con éxito.', 'success')

            except Exception as e:
                db.session.rollback()
                flash(f"Ocurrió un error al eliminar el proyecto: {e}", "danger")

            return redirect(url_for('select_tenant'))

        @app.route("/uploads/<path:filename>")
        def download_file(filename):
            upload_folder_path = os.path.join(project_root, app.config["UPLOAD_FOLDER"])
            return send_from_directory(upload_folder_path, filename, as_attachment=True)
        
        # --- Comandos CLI ---
        @app.cli.command("reset-db")
        def reset_db_command():
            """Borra y recrea la base de datos Y la carpeta de subidas."""
            db_path_str = app.config.get('SQLALCHEMY_DATABASE_URI')
            if db_path_str and db_path_str.startswith('sqlite:///'):
                db_path = db_path_str.split('sqlite:///', 1)[1]
                if not os.path.isabs(db_path):
                     db_path = os.path.join(app.instance_path, db_path)
                if os.path.exists(db_path):
                    os.remove(db_path)
                    click.echo(f"Base de datos eliminada: {db_path}")
            
            upload_folder = os.path.join(project_root, app.config.get('UPLOAD_FOLDER'))
            if upload_folder and os.path.exists(upload_folder):
                click.echo(f"Limpiando la carpeta de subidas: {upload_folder}")
                for filename in os.listdir(upload_folder):
                    file_path = os.path.join(upload_folder, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        click.echo(f'Error al borrar {file_path}. Razón: {e}')
            
            click.echo("Creando base de datos desde migraciones...")
            upgrade()
            click.echo("Base de datos y carpeta de subidas reiniciadas con éxito.")
            
    return app