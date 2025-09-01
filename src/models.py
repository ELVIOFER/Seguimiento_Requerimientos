# --- src/models.py (Versión Corregida para SQLite) ---

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import MetaData

# Convención de nombres para las constraints, requerido por Alembic para SQLite
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Creamos una instancia de SQLAlchemy con la convención de nombres
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))


class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    ordenes = db.relationship('Orden', backref='proveedor', lazy=True)


class Requerimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_requerimiento = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_presentacion = db.Column(db.String(10), nullable=False)
    estado = db.Column(db.String(50), default='En Mesa de Partes')
    archivo_path = db.Column(db.String(200), nullable=True)
    orden = db.relationship(
        'Orden', 
        backref='requerimiento', 
        uselist=False, 
        lazy=True, 
        cascade="all, delete-orphan" # <<<--- AÑADE ESTA LÍNEA
    )


class Orden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    tipo_orden = db.Column(db.String(50), nullable=False)
    fecha_emision = db.Column(db.String(10), nullable=True)
    fecha_notificacion = db.Column(db.String(10), nullable=True)
    plazo_ejecucion_dias = db.Column(db.Integer, nullable=True)
    archivo_orden_path = db.Column(db.String(200), nullable=True)
    
    # Aquí la clave foránea ya tenía unique=True, la convención se encargará de nombrarla
    requerimiento_id = db.Column(db.Integer, db.ForeignKey('requerimiento.id'), unique=True, nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)