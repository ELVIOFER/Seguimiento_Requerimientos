# --- src/routes/requerimiento.py (Versión Final con SQLAlchemy) ---

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
)
# Ya no necesitamos sqlite3 directamente
import os
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError # Importamos la excepción específica de SQLAlchemy

# 1. IMPORTACIONES MODERNIZADAS
from ..models import db, Requerimiento

bp = Blueprint('requerimiento', __name__, url_prefix='/requerimiento')


@bp.route("/nuevo", methods=("GET", "POST"))
def nuevo_requerimiento():
    if request.method == "POST":
        numero = request.form["numero_requerimiento"]
        descripcion = request.form["descripcion"]
        fecha = request.form["fecha_presentacion"]
        
        try:
            archivo_path = None
            if "archivo" in request.files:
                file = request.files["archivo"]
                if file.filename != "":
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                    archivo_path = filename
            
            # 2. CREAR OBJETOS CON SQLAlchemy
            nuevo_req = Requerimiento(
                numero_requerimiento=numero,
                descripcion=descripcion,
                fecha_presentacion=fecha,
                archivo_path=archivo_path
            )
            
            db.session.add(nuevo_req)
            db.session.commit()
            
            flash("Requerimiento creado con éxito.", "success")
            return redirect(url_for("index"))
        
        except IntegrityError: # Usamos la excepción de SQLAlchemy
            db.session.rollback() # Importante: deshacer la transacción fallida
            flash(
                "Error: El número de requerimiento ya existe. Por favor, "
                "ingrese uno diferente.", "danger"
            )
            return render_template("crear_requerimiento.html")
            
    return render_template("crear_requerimiento.html")


@bp.route("/editar/<int:req_id>", methods=("GET", "POST"))
def editar_requerimiento(req_id):
    # 3. OBTENER OBJETOS CON SQLAlchemy
    req = db.session.get(Requerimiento, req_id)
    if not req:
        abort(404)

    if request.method == "POST":
        try:
            # 4. ACTUALIZAR ATRIBUTOS DEL OBJETO
            req.numero_requerimiento = request.form["numero_requerimiento"]
            req.descripcion = request.form["descripcion"]
            req.fecha_presentacion = request.form["fecha_presentacion"]
            req.estado = request.form["estado"]

            if "archivo" in request.files:
                file = request.files["archivo"]
                if file.filename != "":
                    # Borrar archivo antiguo si existe
                    if req.archivo_path and os.path.exists(
                        os.path.join(current_app.config['UPLOAD_FOLDER'], req.archivo_path)
                    ):
                        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], req.archivo_path))
                    
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                    req.archivo_path = filename

            db.session.commit()
            flash("Requerimiento actualizado con éxito.", "success")
            return redirect(url_for("index"))

        except IntegrityError:
            db.session.rollback()
            flash(
                "Error al actualizar: El nuevo número de requerimiento "
                "ya está en uso por otro registro.", "danger"
            )
            return render_template("editar_requerimiento.html", req=req)

    return render_template("editar_requerimiento.html", req=req)


@bp.route("/eliminar/<int:req_id>", methods=("POST",))
def eliminar_requerimiento(req_id):
    req_a_eliminar = db.session.get(Requerimiento, req_id)
    if not req_a_eliminar:
        abort(404)

    # Borrar archivo físico si existe
    if req_a_eliminar.archivo_path:
        ruta_archivo = os.path.join(current_app.config['UPLOAD_FOLDER'], req_a_eliminar.archivo_path)
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)

    # 5. ELIMINAR OBJETOS CON SQLAlchemy
    # Gracias a las relaciones en cascada, al borrar un requerimiento,
    # la orden asociada (si existe) también debería borrarse.
    # SQLAlchemy se encarga de la lógica de DELETE FROM orden...
    db.session.delete(req_a_eliminar)
    db.session.commit()
    
    flash("Requerimiento y sus órdenes asociadas eliminados correctamente.", "info")
    return redirect(url_for("index"))