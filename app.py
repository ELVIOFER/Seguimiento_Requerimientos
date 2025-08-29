# --- Archivo: app.py (Versión final con todas las correcciones y mejoras) ---

import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort, flash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from database import get_db, init_app

app = Flask(__name__)

# --- Configuraciones (sin cambios) ---
app.config['DATABASE'] = 'instance/control_proyectos.sqlite'
os.makedirs(app.instance_path, exist_ok=True)
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui-cambiar-en-produccion'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['POSTS_PER_PAGE'] = 10 

# --- Inicialización (sin cambios) ---
init_app(app)

# --- Funciones de Ayuda ---

def parsear_fecha(fecha_str):
    """
    Convierte una cadena de texto en formato 'YYYY-MM-DD' a un objeto datetime.
    Retorna None si la cadena es nula, está vacía o tiene un formato incorrecto.
    """
    if not fecha_str:
        return None
    try:
        # Intenta convertir la cadena a un objeto de fecha
        return datetime.strptime(fecha_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        # Si el formato es incorrecto o no es una cadena, devuelve None
        print(f"Advertencia: Formato de fecha inválido encontrado: '{fecha_str}'")
        return None
def procesar_item_requerimiento(item):
    item_procesado = dict(item)
    item_procesado['dias_hasta_emision'] = None
    item_procesado['dias_hasta_notificacion'] = None
    item_procesado['fecha_culminacion'] = None

    # Usamos nuestra nueva función para convertir fechas de forma segura
    fecha_presentacion = parsear_fecha(item_procesado.get('fecha_presentacion'))
    fecha_emision = parsear_fecha(item_procesado.get('fecha_emision'))
    fecha_notificacion = parsear_fecha(item_procesado.get('fecha_notificacion'))

    # Ahora la lógica de cálculo es más clara y segura
    if fecha_presentacion and fecha_emision:
        item_procesado['dias_hasta_emision'] = (fecha_emision - fecha_presentacion).days

    if fecha_presentacion and fecha_notificacion:
        item_procesado['dias_hasta_notificacion'] = (fecha_notificacion - fecha_presentacion).days

        plazo_dias = item_procesado.get('plazo_ejecucion_dias')
        # Nos aseguramos de que plazo_dias sea un número antes de usarlo
        if isinstance(plazo_dias, int):
            plazo = timedelta(days=plazo_dias)
            fecha_culminacion_obj = fecha_notificacion + plazo
            item_procesado['fecha_culminacion'] = fecha_culminacion_obj.strftime('%Y-%m-%d')
            
    # El bloque try/except ya no es necesario aquí para las fechas,
    # porque `parsear_fecha` ya maneja los errores de formato.
    # Esto simplifica enormemente la función.

    return item_procesado

def procesar_item_requerimiento(item):
    # ... (código sin cambios)
    item_procesado = dict(item)
    item_procesado['dias_hasta_emision'] = None
    item_procesado['dias_hasta_notificacion'] = None
    item_procesado['fecha_culminacion'] = None
    try:
        fecha_presentacion = datetime.strptime(item_procesado['fecha_presentacion'], '%Y-%m-%d')
        if item_procesado['fecha_emision']:
            fecha_emision = datetime.strptime(item_procesado['fecha_emision'], '%Y-%m-%d')
            item_procesado['dias_hasta_emision'] = (fecha_emision - fecha_presentacion).days
        if item_procesado['fecha_notificacion']:
            fecha_notificacion = datetime.strptime(item_procesado['fecha_notificacion'], '%Y-%m-%d')
            item_procesado['dias_hasta_notificacion'] = (fecha_notificacion - fecha_presentacion).days
            if item_procesado['plazo_ejecucion_dias'] is not None:
                plazo = timedelta(days=item_procesado['plazo_ejecucion_dias'])
                fecha_culminacion_obj = fecha_notificacion + plazo
                item_procesado['fecha_culminacion'] = fecha_culminacion_obj.strftime('%Y-%m-%d')
    except (ValueError, TypeError) as e:
        print(f"Error procesando fechas para el item {item_procesado.get('id')}: {e}")
    return item_procesado

def get_or_create_provider(db, provider_name):
    # ... (código sin cambios)
    provider_name = provider_name.strip()
    proveedor = db.execute(
        'SELECT id FROM proveedor WHERE LOWER(nombre) = LOWER(?)', 
        (provider_name,)
    ).fetchone()
    if proveedor:
        return proveedor['id']
    else:
        cursor = db.execute('INSERT INTO proveedor (nombre) VALUES (?)', (provider_name,))
        return cursor.lastrowid

# --- Rutas Principales (sin cambios) ---
@app.route('/')
def index():
    # ... (código sin cambios)
    page = request.args.get('page', 1, type=int)
    query_search = request.args.get('q')
    sort_by = request.args.get('sort_by', 'fecha_presentacion')
    order = request.args.get('order', 'desc')
    allowed_sort_columns = {'numero_requerimiento': 'r.numero_requerimiento','fecha_presentacion': 'r.fecha_presentacion','estado': 'r.estado'}
    sort_column = allowed_sort_columns.get(sort_by, 'r.fecha_presentacion')
    if order not in ['asc', 'desc']:
        order = 'desc'
    db = get_db()
    params = []
    count_query = "SELECT COUNT(r.id) FROM requerimiento r"
    if query_search:
        count_query += " WHERE r.numero_requerimiento LIKE ? OR r.descripcion LIKE ?"
        params.extend([f"%{query_search}%", f"%{query_search}%"])
    total_items = db.execute(count_query, params).fetchone()[0]
    offset = (page - 1) * app.config['POSTS_PER_PAGE']
    base_query = "SELECT r.id, r.numero_requerimiento, r.descripcion, r.fecha_presentacion, r.estado, r.archivo_path, o.id as orden_id, o.fecha_emision, o.fecha_notificacion, o.monto, o.plazo_ejecucion_dias, p.nombre as proveedor_nombre FROM requerimiento r LEFT JOIN orden o ON r.id = o.requerimiento_id LEFT JOIN proveedor p ON o.proveedor_id = p.id"
    if query_search:
        base_query += " WHERE r.numero_requerimiento LIKE ? OR r.descripcion LIKE ?"
    base_query += f" ORDER BY {sort_column} {order.upper()} LIMIT ? OFFSET ?;"
    params.extend([app.config['POSTS_PER_PAGE'], offset])
    items = db.execute(base_query, params).fetchall()
    resultados_procesados = [procesar_item_requerimiento(item) for item in items]
    return render_template('index.html', resultados=resultados_procesados, page=page, total_items=total_items, per_page=app.config['POSTS_PER_PAGE'], query_search=query_search, sort_by=sort_by, order=order)

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Rutas CRUD para Requerimientos (CON CAMBIOS) ---

@app.route('/requerimiento/nuevo', methods=('GET', 'POST'))
def nuevo_requerimiento():
    if request.method == 'POST':
        numero = request.form['numero_requerimiento']
        descripcion = request.form['descripcion']
        fecha = request.form['fecha_presentacion']
        db = get_db()
        try:
            archivo_path = None
            if 'archivo' in request.files:
                file = request.files['archivo']
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    archivo_path = filename
            db.execute(
                'INSERT INTO requerimiento (numero_requerimiento, descripcion, fecha_presentacion, archivo_path) VALUES (?, ?, ?, ?)',
                (numero, descripcion, fecha, archivo_path)
            )
            db.commit()
            flash('Requerimiento creado con éxito.', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Error: El número de requerimiento ya existe. Por favor, ingrese uno diferente.', 'danger')
            # Devolvemos el formulario con los datos que el usuario ya había ingresado
            return render_template('crear_requerimiento.html')
    return render_template('crear_requerimiento.html')

# <<< --- RUTA MEJORADA PARA MANEJAR ERRORES DE DUPLICADO --- >>>
@app.route('/requerimiento/editar/<int:req_id>', methods=('GET', 'POST'))
def editar_requerimiento(req_id):
    db = get_db()
    requerimiento = db.execute('SELECT * FROM requerimiento WHERE id = ?', (req_id,)).fetchone()
    
    if request.method == 'POST':
        numero = request.form['numero_requerimiento']
        descripcion = request.form['descripcion']
        fecha = request.form['fecha_presentacion']
        estado = request.form['estado']
        
        try: # <<<--- AÑADIDO
            archivo_antiguo_path = requerimiento['archivo_path']
            nuevo_archivo_path = archivo_antiguo_path 
            if 'archivo' in request.files:
                file = request.files['archivo']
                if file.filename != '':
                    if archivo_antiguo_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], archivo_antiguo_path)):
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], archivo_antiguo_path))
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    nuevo_archivo_path = filename
            
            db.execute(
                'UPDATE requerimiento SET numero_requerimiento = ?, descripcion = ?, fecha_presentacion = ?, estado = ?, archivo_path = ? WHERE id = ?',
                (numero, descripcion, fecha, estado, nuevo_archivo_path, req_id)
            )
            db.commit()
            flash('Requerimiento actualizado con éxito.', 'success')
            return redirect(url_for('index'))
            
        except sqlite3.IntegrityError: # <<<--- AÑADIDO
            flash('Error al actualizar: El nuevo número de requerimiento ya está en uso por otro registro.', 'danger')
            # Volvemos a renderizar la página de edición para que el usuario pueda corregir
            return render_template('editar_requerimiento.html', req=requerimiento)

    return render_template('editar_requerimiento.html', req=requerimiento)

@app.route('/requerimiento/eliminar/<int:req_id>', methods=('POST',))
def eliminar_requerimiento(req_id):
    # ... (código sin cambios)
    db = get_db()
    db.execute('DELETE FROM orden WHERE requerimiento_id = ?', (req_id,))
    db.execute('DELETE FROM requerimiento WHERE id = ?', (req_id,))
    db.commit()
    flash('Requerimiento eliminado correctamente.', 'info')
    return redirect(url_for('index'))

# --- Rutas CRUD para Órdenes (sin cambios) ---
@app.route('/orden/crear/<int:req_id>', methods=('GET', 'POST'))
def crear_orden(req_id):
    # ... (código sin cambios)
    db = get_db()
    requerimiento = db.execute('SELECT * FROM requerimiento WHERE id = ?', (req_id,)).fetchone()
    if request.method == 'POST':
        proveedor_nombre = request.form['proveedor_nombre']
        monto = request.form['monto']
        tipo = request.form['tipo_orden']
        emision = request.form['fecha_emision']
        notificacion = request.form['fecha_notificacion']
        plazo = request.form['plazo_ejecucion_dias']
        proveedor_id = get_or_create_provider(db, proveedor_nombre)
        db.execute('INSERT INTO orden (requerimiento_id, proveedor_id, monto, tipo_orden, fecha_emision, fecha_notificacion, plazo_ejecucion_dias) VALUES (?, ?, ?, ?, ?, ?, ?)', (req_id, proveedor_id, monto, tipo, emision, notificacion, plazo))
        db.execute("UPDATE requerimiento SET estado = 'Con Orden Emitida' WHERE id = ?", (req_id,))
        db.commit()
        flash(f'Orden creada para el requerimiento {requerimiento["numero_requerimiento"]}.', 'success')
        return redirect(url_for('index'))
    proveedores_rows = db.execute('SELECT nombre FROM proveedor ORDER BY nombre').fetchall()
    proveedores = [row['nombre'] for row in proveedores_rows]
    return render_template('crear_orden.html', requerimiento=requerimiento, proveedores=proveedores)

@app.route('/orden/<int:orden_id>')
def orden_detalle(orden_id):
    # ... (código sin cambios)
    db = get_db()
    query = "SELECT o.*, p.nombre as proveedor_nombre, r.numero_requerimiento, r.descripcion as requerimiento_descripcion, r.archivo_path as requerimiento_archivo_path FROM orden o LEFT JOIN proveedor p ON o.proveedor_id = p.id LEFT JOIN requerimiento r ON o.requerimiento_id = r.id WHERE o.id = ?"
    orden = db.execute(query, (orden_id,)).fetchone()
    if orden is None:
        abort(404)
    return render_template('ver_orden.html', orden=orden)

@app.route('/orden/editar/<int:orden_id>', methods=('POST',))
def editar_orden(orden_id):
    # ... (código sin cambios)
    db = get_db()
    proveedor_nombre = request.form['proveedor_nombre']
    monto = request.form['monto']
    tipo = request.form['tipo_orden']
    emision = request.form['fecha_emision']
    notificacion = request.form['fecha_notificacion']
    plazo = request.form['plazo_ejecucion_dias']
    cursor = db.execute('SELECT archivo_orden_path FROM orden WHERE id = ?', (orden_id,))
    orden_actual = cursor.fetchone()
    archivo_antiguo_path = orden_actual['archivo_orden_path'] if orden_actual else None
    nuevo_archivo_path = archivo_antiguo_path
    if 'archivo_orden' in request.files:
        file = request.files['archivo_orden']
        if file.filename != '':
            if archivo_antiguo_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], archivo_antiguo_path)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], archivo_antiguo_path))
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            nuevo_archivo_path = filename
    proveedor_id = get_or_create_provider(db, proveedor_nombre)
    db.execute("UPDATE orden SET proveedor_id = ?, monto = ?, tipo_orden = ?, fecha_emision = ?, fecha_notificacion = ?, plazo_ejecucion_dias = ?, archivo_orden_path = ? WHERE id = ?", (proveedor_id, monto, tipo, emision, notificacion, plazo, nuevo_archivo_path, orden_id))
    db.commit()
    flash('Los cambios en la orden han sido guardados.', 'success')
    return redirect(url_for('orden_detalle', orden_id=orden_id))

if __name__ == '__main__':
    app.run(debug=True)