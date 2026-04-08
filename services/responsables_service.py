import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.BD_Client import get_supabase

def login_responsable(correo: str, contrasena: str):
    sb = get_supabase()
    resp = (sb.table("Responsables")
              .select("*")
              .eq("correo", correo)
              .eq("contraseña", contrasena)
              .execute())
    if resp.data:
        return resp.data[0]
    return None