# --- src/routes/orden.py (Versión Final con SQLAlchemy) ---

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
)
import os
from werkzeug.utils import secure_filename

# 1. IMPORTACIONES MODERNIZADAS
# Importamos la instancia 'db' y los Modelos que necesitamos
from ..models import db, Requerimiento, Orden, Proveedor 
# Importamos nuestra nueva función de ayuda refactorizada
from ..database import get_or_create_provider

bp = Blueprint('orden', __name__, url_prefix='/orden')


@bp.route("/crear/<int:req_id>", methods=("GET", "POST"))
def crear_orden(req_id):
    # 2. OBTENER OBJETOS CON SQLAlchemy (mucho más limpio)
    # db.session.get() es la forma moderna de buscar un objeto por su clave primaria.
    requerimiento = db.session.get(Requerimiento, req_id)
    if not requerimiento:
        abort(404)

    if request.method == "POST":
        proveedor_nombre = request.form["proveedor_nombre"]
        
        # 3. USAR LA NUEVA FUNCIÓN DE AYUDA
        # Le pasamos la sesión, el Modelo y el nombre. Devuelve un objeto Proveedor.
        proveedor = get_or_create_provider(db.session, Proveedor, proveedor_nombre)
        
        # 4. CREAR OBJETOS EN LUGAR DE INSERTAR SQL
        # Creamos una instancia de nuestra clase Orden y le pasamos los datos.
        nueva_orden = Orden(
            requerimiento=requerimiento,
            proveedor=proveedor,
            monto=request.form["monto"],
            tipo_orden=request.form["tipo_orden"],
            fecha_emision=request.form["fecha_emision"],
            fecha_notificacion=request.form["fecha_notificacion"],
            plazo_ejecucion_dias=request.form["plazo_ejecucion_dias"]
        )
        
        # 5. GUARDAR EN LA BASE DE DATOS
        db.session.add(nueva_orden) # Añade el nuevo objeto a la "sesión" de cambios.
        db.session.commit()      # Confirma y guarda todos los cambios en la BD.
        
        flash(f'Orden creada para el requerimiento {requerimiento.numero_requerimiento}.', "success")
        return redirect(url_for("index"))
        
    # La consulta para el datalist también usa SQLAlchemy ahora
    proveedores_rows = db.session.query(Proveedor.nombre).order_by(Proveedor.nombre).all()
    proveedores = [row.nombre for row in proveedores_rows]
    
    return render_template(
        "crear_orden.html", requerimiento=requerimiento, proveedores=proveedores
    )


@bp.route("/<int:orden_id>")
def orden_detalle(orden_id):
    # ¡Mira qué simple es ahora obtener una orden con sus relaciones!
    orden = db.session.get(Orden, orden_id)
    if orden is None:
        abort(404)
    # En la plantilla podemos acceder a 'orden.requerimiento.numero_requerimiento'
    # o 'orden.proveedor.nombre' gracias a las relaciones definidas en los modelos.
    return render_template("ver_orden.html", orden=orden)


@bp.route("/editar/<int:orden_id>", methods=("POST",))
def editar_orden(orden_id):
    orden_a_editar = db.session.get(Orden, orden_id)
    if not orden_a_editar:
        abort(404)

    proveedor_nombre = request.form["proveedor_nombre"]
    proveedor = get_or_create_provider(db.session, Proveedor, proveedor_nombre)

    # 6. ACTUALIZAR OBJETOS DIRECTAMENTE
    # En lugar de un UPDATE, simplemente modificamos los atributos del objeto.
    orden_a_editar.proveedor = proveedor
    orden_a_editar.monto = request.form["monto"]
    orden_a_editar.tipo_orden = request.form["tipo_orden"]
    orden_a_editar.fecha_emision = request.form["fecha_emision"]
    orden_a_editar.fecha_notificacion = request.form["fecha_notificacion"]
    orden_a_editar.plazo_ejecucion_dias = request.form["plazo_ejecucion_dias"]

    # La lógica para manejar archivos no cambia mucho
    if "archivo_orden" in request.files:
        file = request.files["archivo_orden"]
        if file.filename != "":
            # Borramos el archivo antiguo si existe
            if orden_a_editar.archivo_orden_path and os.path.exists(
                os.path.join(current_app.config["UPLOAD_FOLDER"], orden_a_editar.archivo_orden_path)
            ):
                os.remove(
                    os.path.join(current_app.config["UPLOAD_FOLDER"], orden_a_editar.archivo_orden_path)
                )
            
            # Guardamos el nuevo archivo
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            orden_a_editar.archivo_orden_path = filename # Actualizas el path

    db.session.commit() # Un solo commit guarda todos los cambios.
    
    flash("Los cambios en la orden han sido guardados.", "success")
    return redirect(url_for("orden.orden_detalle", orden_id=orden_id))