# Seguimiento de Requerimientos

Una aplicación web desarrollada con Flask para gestionar y dar seguimiento a los requerimientos de un proyecto de inversion. Permite a los usuarios crear, visualizar, actualizar y marcar requerimientos como completados.

## ✨ Características Principales (Features)

*   **Creación de Requerimientos:** Añade nuevos requerimientos con detalles como título, descripción y prioridad.
*   **Listado Centralizado:** Visualiza todos los requerimientos en una tabla o lista clara y ordenada.
*   **Actualización de Estado:** Modifica el estado de un requerimiento (Ej: Pendiente, En Progreso, Completado).
*   **Interfaz Sencilla:** Diseño limpio y fácil de usar para una gestión eficiente.

## 🛠️ Tecnologías Utilizadas (Tech Stack)

*   **Backend:** Python, Flask
*   **Base de Datos:** SQLite 
*   **Frontend:** HTML, CSS 

## 🚀 Instalación y Puesta en Marcha

Sigue estos pasos para tener una copia del proyecto funcionando en tu máquina local.

1.  **Clona el repositorio**
    ```bash
    git clone https://github.com/ELVIOFER/Seguimiento_Requerimientos.git
    ```

2.  **Navega al directorio del proyecto**
    ```bash
    cd Seguimiento_Requerimientos
    ```

3.  **Crea y activa un entorno virtual**
    ```bash
    # Crear el entorno
    python -m venv venv

    # Activar en Windows
    .\venv\Scripts\activate

    # Activar en Mac/Linux
    source venv/bin/activate
    ```

4.  **Instala las dependencias**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Inicializa la base de datos** (Si tienes un script para esto)
    ```bash
    # Por ejemplo, si tienes un script init_db.py
    python init_db.py
    ```

## 🏃‍♂️ Uso

Una vez completada la instalación, puedes ejecutar la aplicación con el siguiente comando:

```bash
flask run