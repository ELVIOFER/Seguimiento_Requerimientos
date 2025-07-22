# init_db.py (Versión 2)
import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

# --- NUEVO: Insertar proveedores de ejemplo ---
cursor = connection.cursor()
cursor.execute("INSERT INTO proveedor (nombre, ruc, contacto) VALUES (?, ?, ?)",
               ('Servicios Generales XYZ S.A.C.', '20123456789', 'juan.perez@xyz.com'))
cursor.execute("INSERT INTO proveedor (nombre, ruc, contacto) VALUES (?, ?, ?)",
               ('Tecnología y Soluciones TechNova', '20987654321', 'ventas@technova.pe'))
# ---------------------------------------------

connection.commit()
connection.close()

print("La base de datos ha sido inicializada y se han añadido proveedores de ejemplo.")