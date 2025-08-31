# --- src/routes/requerimiento.py (CONTENIDO FINAL) ---

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app
)
import sqlite3
import os
from werkzeug.utils import secure_filename
from ..database import get_db

bp = Blueprint('requerimiento', __name__, url_prefix='/requerimiento')


@bp.route("/nuevo", methods=("GET", "POST"))
def nuevo_requerimiento():
    if request.method == "POST":
        numero = request.form["numero_requerimiento"]
        descripcion = request.form["descripcion"]
        fecha = request.form["fecha_presentacion"]
        db = get_db()
        try:
            archivo_path = None
            if "archivo" in request.files:
                file = request.files["archivo"]
                if file.filename != "":
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                    archivo_path = filename
            db.execute(
                "INSERT INTO requerimiento (numero_requerimiento, "
                "descripcion, fecha_presentacion, archivo_path) VALUES (?, ?, ?, ?)",
                (numero, descripcion, fecha, archivo_path),
            )
            db.commit()
            flash("Requerimiento creado con éxito.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash(
                "Error: El número de requerimiento ya existe. Por favor, "
                "ingrese uno diferente.",
                "danger",
            )
            return render_template("crear_requerimiento.html")
    return render_template("crear_requerimiento.html")


@bp.route("/editar/<int:req_id>", methods=("GET", "POST"))
def editar_requerimiento(req_id):
    db = get_db()
    requerimiento = db.execute(
        "SELECT * FROM requerimiento WHERE id = ?", (req_id,)
    ).fetchone()

    if request.method == "POST":
        numero = request.form["numero_requerimiento"]
        descripcion = request.form["descripcion"]
        fecha = request.form["fecha_presentacion"]
        estado = request.form["estado"]

        try:
            archivo_antiguo_path = requerimiento["archivo_path"]
            nuevo_archivo_path = archivo_antiguo_path
            if "archivo" in request.files:
                file = request.files["archivo"]
                if file.filename != "":
                    if archivo_antiguo_path and os.path.exists(
                        os.path.join(current_app.config["UPLOAD_FOLDER"], archivo_antiguo_path)
                    ):
                        os.remove(
                            os.path.join(
                                current_app.config["UPLOAD_FOLDER"], archivo_antiguo_path
                            )
                        )
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                    nuevo_archivo_path = filename

            db.execute(
                "UPDATE requerimiento SET numero_requerimiento = ?, descripcion = ?, "
                "fecha_presentacion = ?, estado = ?, archivo_path = ? WHERE id = ?",
                (numero, descripcion, fecha, estado, nuevo_archivo_path, req_id),
            )
            db.commit()
            flash("Requerimiento actualizado con éxito.", "success")
            return redirect(url_for("index"))

        except sqlite3.IntegrityError:
            flash(
                "Error al actualizar: El nuevo número de requerimiento "
                "ya está en uso por otro registro.",
                "danger",
            )
            return render_template("editar_requerimiento.html", req=requerimiento)

    return render_template("editar_requerimiento.html", req=requerimiento)


@bp.route("/eliminar/<int:req_id>", methods=("POST",))
def eliminar_requerimiento(req_id):
    db = get_db()
    req = db.execute("SELECT archivo_path FROM requerimiento WHERE id = ?", (req_id,)).fetchone()
    if req and req['archivo_path']:
        ruta_archivo = os.path.join(current_app.config['UPLOAD_FOLDER'], req['archivo_path'])
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
            
    db.execute("DELETE FROM orden WHERE requerimiento_id = ?", (req_id,))
    db.execute("DELETE FROM requerimiento WHERE id = ?", (req_id,))
    db.commit()
    flash("Requerimiento y archivo asociado eliminados correctamente.", "info")
    return redirect(url_for("index"))