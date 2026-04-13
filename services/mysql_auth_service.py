import mysql.connector

from config.BD_Client import get_connection
from utils.auth import verify_password


def login_responsable(correo: str, contrasena: str):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, nom_res, correo, password_hash, rol, estado, fecha_creacion
            FROM responsables
            WHERE correo = %s
            LIMIT 1
            """,
            (correo,),
        )
        usuario = cursor.fetchone()

        if not usuario or usuario["estado"] != "activo":
            return None

        password_guardado = usuario["password_hash"]

        # Compatibilidad temporal: acepta contraseña en texto plano o en hash SHA-256.
        if contrasena == password_guardado or verify_password(contrasena, password_guardado):
            return {
                "id": usuario["id"],
                "nom_res": usuario["nom_res"],
                "correo": usuario["correo"],
                "rol": usuario["rol"],
                "estado": usuario["estado"],
                "fecha_creacion": usuario["fecha_creacion"],
            }
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def crear_responsable(nom_res: str, correo: str, contrasena: str, rol: str = "trabajador"):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO responsables (nom_res, correo, password_hash, rol)
            VALUES (%s, %s, %s, %s)
            """,
            (nom_res, correo, contrasena, rol),
        )
        conn.commit()
        return {"exito": True, "id": cursor.lastrowid}
    except mysql.connector.IntegrityError as exc:
        return {"exito": False, "mensaje": f"No se pudo crear el usuario: {exc.msg}"}
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
