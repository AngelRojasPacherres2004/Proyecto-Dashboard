import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from config.BD_Client import init_db
from pages import login

# Inicializar la base de datos
init_db()


if __name__ == "__main__":
    login.login_page()
