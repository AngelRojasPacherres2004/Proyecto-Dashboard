import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)


def get_connection():
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER", "dashboard_user")
    db_password = os.getenv("DB_PASSWORD", "dashboard123")
    db_name = os.getenv("DB_NAME", "dashboard_proyectos")

    # En XAMPP suele usarse root sin contraseña.
    if db_password in {"your-password", "tu-password", "changeme"}:
        db_password = ""

    connection_kwargs = {
        "host": db_host,
        "port": db_port,
        "user": db_user,
        "database": db_name,
        "autocommit": False,
    }

    # Si la contraseña está vacía, no la enviamos para evitar herencias raras.
    if db_password:
        connection_kwargs["password"] = db_password

    return mysql.connector.connect(**connection_kwargs)


def test_connection():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE(), VERSION()")
        db_name, version = cursor.fetchone()
        return {"ok": True, "database": db_name, "version": version}
    finally:
        conn.close()
