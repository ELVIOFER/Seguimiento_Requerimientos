# --- src/forms.py (Actualizado con DocumentoForm) ---

from flask_wtf import FlaskForm
# ===> AÑADIMOS LOS NUEVOS TIPOS DE CAMPO Y VALIDADORES <===
from wtforms import StringField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Optional
# =========================================================

class TenantForm(FlaskForm):
    """Formulario para crear un nuevo Proyecto/Inquilino."""
    name = StringField(
        'Nombre del Proyecto', 
        validators=[
            DataRequired(message="El nombre es obligatorio."),
            Length(min=3, max=100, message="El nombre debe tener entre 3 y 100 caracteres.")
        ]
    )
    submit = SubmitField('Crear Proyecto')


# ===> AQUÍ ESTÁ EL NUEVO FORMULARIO AÑADIDO <===
class DocumentoForm(FlaskForm):
    """Formulario para crear y editar documentos."""
    tipo = SelectField(
        'Tipo de Documento',
        choices=[('Recibido', 'Recibido'), ('Emitido', 'Emitido')],
        validators=[DataRequired(message="Debe seleccionar un tipo.")]
    )
    numero_doc = StringField(
        'Número/Código del Documento',
        validators=[DataRequired(message="Este campo es obligatorio."), Length(max=100)]
    )
    # El format='%Y-%m-%d' es crucial para que el navegador y WTForms se entiendan
    fecha_doc = DateField(
        'Fecha del Documento',
        format='%Y-%m-%d',
        validators=[DataRequired(message="Por favor, seleccione una fecha.")]
    )
    remitente_destinatario = StringField(
        'Remitente / Destinatario',
        validators=[DataRequired(message="Este campo es obligatorio."), Length(max=200)]
    )
    asunto = TextAreaField(
        'Asunto',
        validators=[DataRequired(message="El asunto es obligatorio.")]
    )
    # Usamos 'Optional()' para que el campo no sea obligatorio
    fecha_limite_respuesta = DateField(
        'Fecha Límite para Respuesta',
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    observaciones = TextAreaField(
        'Observaciones',
        validators=[Optional()]
    )
    submit = SubmitField('Guardar Documento')

# ====================================================