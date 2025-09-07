# --- src/models.py (Actualizado con el modelo Documento) ---

from flask_sqlalchemy import SQLAlchemy
from flask import g
from sqlalchemy.schema import MetaData
from sqlalchemy.orm import declared_attr, Session
# ===> AÑADIMOS 'Date' y 'DateTime' para los nuevos campos de fecha <===
from sqlalchemy import event, Date, DateTime

# Convención de nombres
naming_convention = {
    "ix": 'ix_%(column_0_label)s', "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# 1. Creamos una instancia de SQLAlchemy normal.
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))

# 2. Definimos todos nuestros modelos
class Tenant(db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, comment="Nombre único del inquilino/cliente")
    created_at = db.Column(DateTime, server_default=db.func.now())

class TenantScopedMixin:
    @declared_attr
    def tenant_id(cls):
        return db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    @declared_attr
    def tenant(cls):
        return db.relationship('Tenant')

class Proveedor(db.Model, TenantScopedMixin):
    __tablename__ = 'proveedor'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ordenes = db.relationship('Orden', backref='proveedor', lazy=True)

class Requerimiento(db.Model, TenantScopedMixin):
    __tablename__ = 'requerimiento'
    id = db.Column(db.Integer, primary_key=True)
    numero_requerimiento = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_presentacion = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(50), default='En Mesa de Partes')
    archivo_path = db.Column(db.String(300), nullable=True) # Aumentado el tamaño
    orden = db.relationship('Orden', backref='requerimiento', uselist=False, lazy=True, cascade="all, delete-orphan")

class Orden(db.Model, TenantScopedMixin):
    __tablename__ = 'orden'
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    tipo_orden = db.Column(db.String(50), nullable=False)
    fecha_emision = db.Column(db.Date, nullable=True)
    fecha_notificacion = db.Column(db.Date, nullable=True)
    plazo_ejecucion_dias = db.Column(db.Integer, nullable=True)
    archivo_orden_path = db.Column(db.String(300), nullable=True) # Aumentado el tamaño
    requerimiento_id = db.Column(db.Integer, db.ForeignKey('requerimiento.id'), unique=True, nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)

# ===> AÑADIMOS EL NUEVO MODELO PARA EL TRÁMITE DOCUMENTARIO <===
class Documento(db.Model, TenantScopedMixin):
    __tablename__ = 'documentos'
    id = db.Column(db.Integer, primary_key=True)
    
    # --- Datos Básicos ---
    tipo = db.Column(db.String(50), nullable=False, index=True)  # "Emitido" o "Recibido"
    numero_doc = db.Column(db.String(100), nullable=False)
    asunto = db.Column(db.Text, nullable=False)
    fecha_doc = db.Column(Date, nullable=False) # Usando el tipo de dato correcto
    remitente_destinatario = db.Column(db.String(200), comment="Quién lo envía o a quién se envía")
    
    # --- Trazabilidad y Recordatorios ---
    estado = db.Column(db.String(50), nullable=False, default='Pendiente', index=True) # Ej: Pendiente, Respondido, Cerrado
    fecha_limite_respuesta = db.Column(Date, nullable=True) # Para los recordatorios
    observaciones = db.Column(db.Text, nullable=True)
    
    # --- Gestión de Archivos ---
    archivo_path = db.Column(db.String(300), nullable=True)
    
    # --- Relación Padre-Hijo para el seguimiento ---
    documento_padre_id = db.Column(db.Integer, db.ForeignKey('documentos.id'), nullable=True)
    respuestas = db.relationship('Documento', backref=db.backref('documento_padre', remote_side=[id]), lazy='dynamic')

    created_at = db.Column(DateTime, server_default=db.func.now())

# =============================================================

# 3. LÓGICA DE FILTRADO AUTOMÁTICO (sin cambios)
@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    # ... (código sin cambios) ...
    if (
        execute_state.is_select
        and not execute_state.is_column_load
        and not execute_state.is_relationship_load
    ):
        if not g or not hasattr(g, 'tenant_id') or g.tenant_id is None:
            return
        for entity in execute_state.statement.column_descriptions:
            inspection = db.inspect(entity['entity'], raiseerr=False)
            if inspection is not None and 'tenant_id' in inspection.mapper.columns:
                execute_state.statement = execute_state.statement.where(
                    inspection.mapper.c.tenant_id == g.tenant_id
                )
                return

# 4. El evento para la inserción se queda igual (sin cambios)
@event.listens_for(TenantScopedMixin, 'before_insert', propagate=True)
def before_insert_listener(mapper, connection, target):
    # ... (código sin cambios) ...
    if not hasattr(g, 'tenant_id') or g.tenant_id is None:
        raise ValueError("No se puede crear un objeto; no se ha seleccionado ningún proyecto en la sesión.")
    target.tenant_id = g.tenant_id