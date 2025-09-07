# --- src/routes/orden.py (Actualizado para Tipos de Dato Date) ---

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
)
import os

from ..models import db, Requerimiento, Orden, Proveedor
from ..database import get_or_create_provider
# ===> 1. IMPORTAMOS LAS DOS FUNCIONES DE AYUDA <===
from ..logic import save_project_file, parse_date_from_form

bp = Blueprint('orden', __name__, url_prefix='/orden')

@bp.route("/crear/<int:req_id>", methods=("GET", "POST"))
def crear_orden(req_id):
    requerimiento = db.session.get(Requerimiento, req_id)
    if not requerimiento:
        abort(404)

    if request.method == "POST":
        proveedor_nombre = request.form["proveedor_nombre"]
        proveedor = get_or_create_provider(db.session, Proveedor, proveedor_nombre)
        
        relative_path = None
        if "archivo_orden" in request.files:
            file = request.files.get("archivo_orden")
            if file:
                relative_path = save_project_file(file)
        
        # ===> 2. CONVERTIMOS LAS FECHAS ANTES DE GUARDAR <===
        nueva_orden = Orden(
            requerimiento=requerimiento,
            proveedor=proveedor,
            monto=request.form["monto"],
            tipo_orden=request.form["tipo_orden"],
            fecha_emision=parse_date_from_form(request.form.get("fecha_emision")),
            fecha_notificacion=parse_date_from_form(request.form.get("fecha_notificacion")),
            plazo_ejecucion_dias=request.form.get("plazo_ejecucion_dias") or None,
            archivo_orden_path=relative_path
        )
        
        db.session.add(nueva_orden)
        db.session.commit()
        
        flash(f'Orden creada para el requerimiento {requerimiento.numero_requerimiento}.', "success")
        return redirect(url_for("index"))
        
    proveedores_rows = db.session.query(Proveedor.nombre).order_by(Proveedor.nombre).all()
    proveedores = [row.nombre for row in proveedores_rows]
    
    return render_template(
        "crear_orden.html", requerimiento=requerimiento, proveedores=proveedores
    )


@bp.route("/<int:orden_id>")
def orden_detalle(orden_id):
    orden = db.session.get(Orden, orden_id)
    if orden is None:
        abort(404)
    return render_template("ver_orden.html", orden=orden)


@bp.route("/editar/<int:orden_id>", methods=("POST",))
def editar_orden(orden_id):
    orden_a_editar = db.session.get(Orden, orden_id)
    if not orden_a_editar:
        abort(404)

    proveedor_nombre = request.form["proveedor_nombre"]
    proveedor = get_or_create_provider(db.session, Proveedor, proveedor_nombre)

    # ===> 3. CONVERTIMOS LAS FECHAS ANTES DE ACTUALIZAR <===
    orden_a_editar.proveedor = proveedor
    orden_a_editar.monto = request.form["monto"]
    orden_a_editar.tipo_orden = request.form["tipo_orden"]
    orden_a_editar.fecha_emision = parse_date_from_form(request.form.get("fecha_emision"))
    orden_a_editar.fecha_notificacion = parse_date_from_form(request.form.get("fecha_notificacion"))
    orden_a_editar.plazo_ejecucion_dias = request.form.get("plazo_ejecucion_dias") or None

    if "archivo_orden" in request.files:
        file = request.files.get("archivo_orden")
        if file and file.filename != '':
            if orden_a_editar.archivo_orden_path:
                full_old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], orden_a_editar.archivo_orden_path)
                if os.path.exists(full_old_path):
                    os.remove(full_old_path)
            
            new_relative_path = save_project_file(file)
            orden_a_editar.archivo_orden_path = new_relative_path

    db.session.commit()
    
    flash("Los cambios en la orden han sido guardados.", "success")
    return redirect(url_for("orden.orden_detalle", orden_id=orden_id))


@bp.route("/eliminar/<int:orden_id>", methods=("POST",))
def eliminar_orden(orden_id):
    # Esta función no maneja fechas, por lo que no necesita cambios.
    orden_a_eliminar = db.session.get(Orden, orden_id)
    if not orden_a_eliminar:
        abort(404)

    if orden_a_eliminar.archivo_orden_path:
        ruta_completa = os.path.join(current_app.config['UPLOAD_FOLDER'], orden_a_eliminar.archivo_orden_path)
        if os.path.exists(ruta_completa):
            try:
                os.remove(ruta_completa)
                dir_path = os.path.dirname(ruta_completa)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except OSError as e:
                print(f"Error borrando archivo o directorio de orden: {e}")

    db.session.delete(orden_a_eliminar)
    db.session.commit()
    
    flash("La orden ha sido eliminada correctamente.", "info")
    return redirect(url_for("index"))