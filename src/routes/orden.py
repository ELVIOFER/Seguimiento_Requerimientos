# --- src/routes/orden.py (CONTENIDO FINAL) ---

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
)
import os
from werkzeug.utils import secure_filename
from ..database import get_db, get_or_create_provider

bp = Blueprint('orden', __name__, url_prefix='/orden')


@bp.route("/crear/<int:req_id>", methods=("GET", "POST"))
def crear_orden(req_id):
    db = get_db()
    requerimiento = db.execute(
        "SELECT * FROM requerimiento WHERE id = ?", (req_id,)
    ).fetchone()
    if request.method == "POST":
        # ... (código interno sin cambios)
        proveedor_nombre = request.form["proveedor_nombre"]
        monto = request.form["monto"]
        tipo = request.form["tipo_orden"]
        emision = request.form["fecha_emision"]
        notificacion = request.form["fecha_notificacion"]
        plazo = request.form["plazo_ejecucion_dias"]
        proveedor_id = get_or_create_provider(db, proveedor_nombre)
        db.execute(
            "INSERT INTO orden (requerimiento_id, "
            "proveedor_id, monto, tipo_orden, "
            "fecha_emision, fecha_notificacion, "
            "plazo_ejecucion_dias) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (req_id, proveedor_id, monto, tipo, emision, notificacion, plazo),
        )
        db.commit()
        flash(
            f'Orden creada para el requerimiento {requerimiento["numero_requerimiento"]}.',
            "success",
        )
        return redirect(url_for("index"))
    proveedores_rows = db.execute(
        "SELECT nombre FROM proveedor ORDER BY nombre"
    ).fetchall()
    proveedores = [row["nombre"] for row in proveedores_rows]
    return render_template(
        "crear_orden.html", requerimiento=requerimiento, proveedores=proveedores
    )


@bp.route("/<int:orden_id>")
def orden_detalle(orden_id):
    db = get_db()
    query = (
        "SELECT o.*, p.nombre as proveedor_nombre, r.numero_requerimiento, "
        "r.descripcion as requerimiento_descripcion, "
        "r.archivo_path as requerimiento_archivo_path "
        "FROM orden o "
        "LEFT JOIN proveedor p ON o.proveedor_id = p.id "
        "LEFT JOIN requerimiento r ON o.requerimiento_id = r.id "
        "WHERE o.id = ?"
    )
    orden = db.execute(query, (orden_id,)).fetchone()
    if orden is None:
        abort(404)
    return render_template("ver_orden.html", orden=orden)


@bp.route("/editar/<int:orden_id>", methods=("POST",))
def editar_orden(orden_id):
    db = get_db()
    # ... (código interno sin cambios, pero usando current_app.config)
    proveedor_nombre = request.form["proveedor_nombre"]
    monto = request.form["monto"]
    tipo = request.form["tipo_orden"]
    emision = request.form["fecha_emision"]
    notificacion = request.form["fecha_notificacion"]
    plazo = request.form["plazo_ejecucion_dias"]
    cursor = db.execute(
        "SELECT archivo_orden_path FROM orden WHERE id = ?", (orden_id,)
    )
    orden_actual = cursor.fetchone()
    archivo_antiguo_path = orden_actual["archivo_orden_path"] if orden_actual else None
    nuevo_archivo_path = archivo_antiguo_path
    if "archivo_orden" in request.files:
        file = request.files["archivo_orden"]
        if file.filename != "":
            if archivo_antiguo_path and os.path.exists(
                os.path.join(current_app.config["UPLOAD_FOLDER"], archivo_antiguo_path)
            ):
                os.remove(
                    os.path.join(current_app.config["UPLOAD_FOLDER"], archivo_antiguo_path)
                )
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            nuevo_archivo_path = filename
    proveedor_id = get_or_create_provider(db, proveedor_nombre)
    db.execute(
        "UPDATE orden SET proveedor_id = ?, monto = ?, tipo_orden = ?, "
        "fecha_emision = ?, fecha_notificacion = ?, plazo_ejecucion_dias = ?, "
        "archivo_orden_path = ? WHERE id = ?",
        (
            proveedor_id,
            monto,
            tipo,
            emision,
            notificacion,
            plazo,
            nuevo_archivo_path,
            orden_id,
        ),
    )
    db.commit()
    flash("Los cambios en la orden han sido guardados.", "success")
    # Este redirect ahora debe usar el prefijo 'orden.'
    return redirect(url_for("orden.orden_detalle", orden_id=orden_id))