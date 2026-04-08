import os
from pathlib import Path
from typing import Dict, Optional

# Configuración Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Fallback local para desarrollo
DB_PATH = Path(__file__).parent.parent / "data" / "proyecto.db"
DB_PATH.parent.mkdir(exist_ok=True)


def is_supabase_enabled() -> bool:
    """Comprueba si Supabase está configurado en variables de entorno."""
    return bool(SUPABASE_URL and SUPABASE_KEY)


def get_supabase_config() -> Dict[str, Optional[str]]:
    """Devuelve la configuración de Supabase para que el proyecto pueda usarla."""
    return {"url": SUPABASE_URL, "key": SUPABASE_KEY}


def get_connection():
    """Obtiene una conexión a la base de datos.

    Usa SQLite local como fallback. Si Supabase está habilitado,
    el proyecto debe implementar la conexión correspondiente.
    """
    if is_supabase_enabled():
        return None

    import sqlite3

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa la base de datos local cuando no se usa Supabase."""
    if is_supabase_enabled():
        return

    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'trabajador',
            estado TEXT DEFAULT 'activo',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            usuario_id INTEGER NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_vencimiento DATE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rendimiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tareas_completadas INTEGER DEFAULT 0,
            tareas_pendientes INTEGER DEFAULT 0,
            porcentaje_completado REAL DEFAULT 0,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente")
