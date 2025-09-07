# --- src/routes/requerimiento.py (Actualizado para Tipos de Dato Date) ---

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
)
import os
from sqlalchemy.exc import IntegrityError

from ..models import db, Requerimiento
# ===> 1. IMPORTAMOS LAS DOS FUNCIONES DE AYUDA <===
from ..logic import save_project_file, parse_date_from_form

bp = Blueprint('requerimiento', __name__, url_prefix='/requerimiento')


@bp.route("/nuevo", methods=("GET", "POST"))
def nuevo_requerimiento():
    # El formulario vacío se renderiza igual, no hay cambios para peticiones GET
    if request.method == "POST":
        try:
            relative_path = None
            if "archivo" in request.files:
                file = request.files.get("archivo")
                if file:
                    relative_path = save_project_file(file)
            
            # ===> 2. CONVERTIMOS LA FECHA ANTES DE GUARDAR <===
            fecha_presentacion_obj = parse_date_from_form(request.form.get("fecha_presentacion"))
            
            nuevo_req = Requerimiento(
                numero_requerimiento=request.form["numero_requerimiento"],
                descripcion=request.form["descripcion"],
                fecha_presentacion=fecha_presentacion_obj, # Guardamos el objeto Date
                archivo_path=relative_path
            )
            
            db.session.add(nuevo_req)
            db.session.commit()
            
            flash("Requerimiento creado con éxito.", "success")
            return redirect(url_for("index"))
        
        except (IntegrityError, Exception) as e:
            db.session.rollback()
            flash(f"Error al crear el requerimiento: {e}", "danger")
            # Devolvemos los datos ingresados para no perderlos
            return render_template("crear_requerimiento.html", form_data=request.form)
            
    return render_template("crear_requerimiento.html", form_data={})


@bp.route("/editar/<int:req_id>", methods=("GET", "POST"))
def editar_requerimiento(req_id):
    req = db.session.get(Requerimiento, req_id)
    if not req:
        abort(404)

    if request.method == "POST":
        try:
            # ===> 3. CONVERTIMOS LA FECHA ANTES DE ACTUALIZAR <===
            req.numero_requerimiento = request.form["numero_requerimiento"]
            req.descripcion = request.form["descripcion"]
            req.fecha_presentacion = parse_date_from_form(request.form.get("fecha_presentacion"))
            req.estado = request.form["estado"]

            if "archivo" in request.files:
                file = request.files.get("archivo")
                if file and file.filename != '':
                    # Borrar archivo antiguo si existe
                    if req.archivo_path:
                        full_old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], req.archivo_path)
                        if os.path.exists(full_old_path):
                            os.remove(full_old_path)
                    
                    new_relative_path = save_project_file(file)
                    req.archivo_path = new_relative_path

            db.session.commit()
            flash("Requerimiento actualizado con éxito.", "success")
            return redirect(url_for("index"))

        except (IntegrityError, Exception) as e:
            db.session.rollback()
            flash(f"Error al actualizar el requerimiento: {e}", "danger")
            return render_template("editar_requerimiento.html", req=req)

    # Para peticiones GET, pasamos el objeto req a la plantilla
    # La plantilla usará req.fecha_presentacion.strftime('%Y-%m-%d') en el <input>
    return render_template("editar_requerimiento.html", req=req)


@bp.route("/eliminar/<int:req_id>", methods=("POST",))
def eliminar_requerimiento(req_id):
    # Esta función no maneja fechas, por lo que no necesita cambios.
    req_a_eliminar = db.session.get(Requerimiento, req_id)
    if not req_a_eliminar:
        abort(404)

    archivos_a_borrar = []
    if req_a_eliminar.archivo_path:
        archivos_a_borrar.append(req_a_eliminar.archivo_path)
    if req_a_eliminar.orden and req_a_eliminar.orden.archivo_orden_path:
        archivos_a_borrar.append(req_a_eliminar.orden.archivo_orden_path)

    dir_path = None

    for ruta_relativa in archivos_a_borrar:
        ruta_completa = os.path.join(current_app.config['UPLOAD_FOLDER'], ruta_relativa)
        if not dir_path and os.path.exists(ruta_completa):
            dir_path = os.path.dirname(ruta_completa)
        
        if os.path.exists(ruta_completa):
            try:
                os.remove(ruta_completa)
            except OSError as e:
                print(f"Error borrando archivo {ruta_completa}: {e}")

    db.session.delete(req_a_eliminar)
    db.session.commit()
    
    if dir_path and os.path.exists(dir_path) and not os.listdir(dir_path):
        try:
            os.rmdir(dir_path)
        except OSError as e:
            print(f"Error borrando directorio vacío {dir_path}: {e}")
    
    flash("Requerimiento y sus archivos asociados eliminados correctamente.", "info")
    return redirect(url_for("index"))