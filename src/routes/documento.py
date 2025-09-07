# --- src/routes/documento.py (Con Búsqueda y Alertas Visuales) ---

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
import os
# ===> 1. IMPORTAMOS 'date' PARA LOS CÁLCULOS DE URGENCIA <===
from datetime import date
from ..models import db, Documento
from ..forms import DocumentoForm
from ..logic import save_project_file

# Creamos el Blueprint para este módulo
bp = Blueprint('documento', __name__, url_prefix='/documentos')

# ===> 2. FUNCIÓN 'dashboard' ACTUALIZADA CON BÚSQUEDA Y FECHA <===
@bp.route('/')
def dashboard():
    """
    Dashboard principal de Trámite Documentario.
    Muestra los documentos pendientes y un historial, con búsqueda.
    """
    query_search = request.args.get("q")

    # Base de la consulta para documentos recibidos
    recibidos_query = db.session.query(Documento).filter(
        Documento.tipo == 'Recibido',
        Documento.estado.notin_(['Cerrado', 'Archivado'])
    )

    # Base de la consulta para documentos emitidos
    emitidos_query = db.session.query(Documento).filter(
        Documento.tipo == 'Emitido'
    )

    # Si hay un término de búsqueda, lo aplicamos a ambas consultas
    if query_search:
        search_term = f"%{query_search}%"
        search_filter = db.or_(
            Documento.numero_doc.like(search_term),
            Documento.asunto.like(search_term),
            Documento.remitente_destinatario.like(search_term)
        )
        recibidos_query = recibidos_query.filter(search_filter)
        emitidos_query = emitidos_query.filter(search_filter)

    # Ejecutamos las consultas finales con su ordenamiento
    documentos_recibidos_pendientes = recibidos_query.order_by(Documento.fecha_limite_respuesta.asc()).all()
    ultimos_documentos_emitidos = emitidos_query.order_by(Documento.created_at.desc()).limit(10).all()
    
    # Pasamos las variables a la plantilla
    return render_template('documento/dashboard.html', 
                           recibidos=documentos_recibidos_pendientes, 
                           emitidos=ultimos_documentos_emitidos,
                           query_search=query_search,
                           today=date.today()) # Pasamos la fecha de hoy para las alertas

@bp.route('/nuevo', methods=('GET', 'POST'))
def nuevo_documento():
    # ... (código sin cambios) ...
    form = DocumentoForm()
    if form.validate_on_submit():
        try:
            relative_path = save_project_file(request.files.get("archivo"))
            nuevo_doc = Documento(
                tipo=form.tipo.data,
                numero_doc=form.numero_doc.data,
                fecha_doc=form.fecha_doc.data,
                remitente_destinatario=form.remitente_destinatario.data,
                asunto=form.asunto.data,
                fecha_limite_respuesta=form.fecha_limite_respuesta.data,
                observaciones=form.observaciones.data,
                archivo_path=relative_path
            )
            db.session.add(nuevo_doc)
            db.session.commit()
            flash(f'Documento "{nuevo_doc.numero_doc}" registrado con éxito.', 'success')
            return redirect(url_for('documento.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al registrar el documento: {e}', 'danger')
    return render_template('documento/crear_documento.html', form=form, title="Registrar Documento")

@bp.route('/ver/<int:doc_id>')
def ver_documento(doc_id):
    # ... (código sin cambios) ...
    documento = db.session.get(Documento, doc_id)
    if not documento:
        abort(404)
    respuestas_ordenadas = documento.respuestas.order_by(Documento.created_at.asc()).all()
    return render_template('documento/ver_documento.html', 
                           documento=documento, 
                           respuestas=respuestas_ordenadas)

@bp.route('/responder/<int:doc_id>', methods=('GET', 'POST'))
def responder_documento(doc_id):
    # ... (código sin cambios) ...
    documento_padre = db.session.get(Documento, doc_id)
    if not documento_padre:
        abort(404)
    form = DocumentoForm()
    if form.validate_on_submit():
        try:
            relative_path = save_project_file(request.files.get("archivo"))
            documento_respuesta = Documento(
                tipo=form.tipo.data,
                numero_doc=form.numero_doc.data,
                fecha_doc=form.fecha_doc.data,
                remitente_destinatario=form.remitente_destinatario.data,
                asunto=form.asunto.data,
                observaciones=form.observaciones.data,
                archivo_path=relative_path,
                documento_padre_id=documento_padre.id
            )
            documento_padre.estado = 'Respondido'
            db.session.add(documento_respuesta)
            db.session.add(documento_padre)
            db.session.commit()
            flash(f'Respuesta "{documento_respuesta.numero_doc}" registrada con éxito.', 'success')
            return redirect(url_for('documento.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al registrar la respuesta: {e}', 'danger')
    form.tipo.data = 'Emitido'
    form.remitente_destinatario.data = documento_padre.remitente_destinatario
    form.asunto.data = f"Resp. a: {documento_padre.asunto}"
    return render_template('documento/responder.html', 
                           form=form, 
                           documento_padre=documento_padre,
                           title="Responder a Documento")

@bp.route('/editar/<int:doc_id>', methods=('GET', 'POST'))
def editar_documento(doc_id):
    # ... (código sin cambios) ...
    documento = db.session.get(Documento, doc_id)
    if not documento:
        abort(404)
    form = DocumentoForm(obj=documento)
    if form.validate_on_submit():
        try:
            documento.tipo = form.tipo.data
            documento.numero_doc = form.numero_doc.data
            documento.fecha_doc = form.fecha_doc.data
            documento.remitente_destinatario = form.remitente_destinatario.data
            documento.asunto = form.asunto.data
            documento.fecha_limite_respuesta = form.fecha_limite_respuesta.data
            documento.observaciones = form.observaciones.data
            if "archivo" in request.files:
                file = request.files.get("archivo")
                if file and file.filename != '':
                    if documento.archivo_path:
                        full_old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], documento.archivo_path)
                        if os.path.exists(full_old_path):
                            os.remove(full_old_path)
                    new_relative_path = save_project_file(file)
                    documento.archivo_path = new_relative_path
            db.session.commit()
            flash(f'Documento "{documento.numero_doc}" actualizado con éxito.', 'success')
            return redirect(url_for('documento.ver_documento', doc_id=documento.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al actualizar el documento: {e}', 'danger')
    return render_template('documento/editar_documento.html', form=form, documento=documento, title="Editar Documento")

@bp.route('/cambiar-estado/<int:doc_id>', methods=('POST',))
def cambiar_estado(doc_id):
    # ... (código sin cambios) ...
    nuevo_estado = request.form.get('estado')
    estados_validos = ['Pendiente', 'Respondido', 'Cerrado', 'Archivado']
    if not nuevo_estado or nuevo_estado not in estados_validos:
        flash('Se proporcionó un estado inválido.', 'danger')
        return redirect(request.referrer or url_for('documento.dashboard'))
    documento = db.session.get(Documento, doc_id)
    if not documento:
        abort(404)
    documento.estado = nuevo_estado
    try:
        db.session.commit()
        flash(f'El estado del documento "{documento.numero_doc}" se actualizó a "{nuevo_estado}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error al cambiar el estado: {e}', 'danger')
    return redirect(url_for('documento.ver_documento', doc_id=doc_id))

@bp.route('/eliminar/<int:doc_id>', methods=('POST',))
def eliminar_documento(doc_id):
    # ... (código sin cambios) ...
    doc_a_eliminar = db.session.get(Documento, doc_id)
    if not doc_a_eliminar:
        abort(404)
    if doc_a_eliminar.respuestas.first():
        flash('No se puede eliminar un documento que ya tiene respuestas. Por favor, elimine las respuestas primero.', 'danger')
        return redirect(url_for('documento.ver_documento', doc_id=doc_id))
    padre_id = doc_a_eliminar.documento_padre_id
    if doc_a_eliminar.archivo_path:
        ruta_completa = os.path.join(current_app.config['UPLOAD_FOLDER'], doc_a_eliminar.archivo_path)
        if os.path.exists(ruta_completa):
            try:
                os.remove(ruta_completa)
                dir_path = os.path.dirname(ruta_completa)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except OSError as e:
                print(f"Error borrando archivo o directorio de documento: {e}")
    db.session.delete(doc_a_eliminar)
    redirect_url = url_for('documento.dashboard')
    if padre_id:
        documento_padre = db.session.get(Documento, padre_id)
        if documento_padre:
            if documento_padre.respuestas.count() == 0:
                documento_padre.estado = 'Pendiente'
            redirect_url = url_for('documento.ver_documento', doc_id=padre_id)
    db.session.commit()
    flash(f'Documento eliminado correctamente.', 'info')
    return redirect(redirect_url)