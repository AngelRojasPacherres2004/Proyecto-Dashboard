import streamlit as st
import sys
from pathlib import Path

from config.BD_Client import get_connection
from utils.auth import verify_password

# Agregar la raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))


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


def login_page():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario = None

    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 50px auto;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🔐 Dashboard de Proyectos")
    st.write("---")
    st.subheader("Inicia sesión en tu cuenta")

    with st.form("login_form"):
        correo = st.text_input(
            "📧 Correo",
            placeholder="Ingresa tu correo"
        )
        password = st.text_input(
            "🔑 Contraseña",
            type="password",
            placeholder="Ingresa tu contraseña"
        )
        submit_login = st.form_submit_button("Iniciar Sesión", use_container_width=True)

    if submit_login:
        if not correo or not password:
            st.error("⚠️ Por favor completa todos los campos")
        else:
            with st.spinner("Verificando credenciales..."):
                usuario = login_responsable(correo, password)

            if usuario:
                st.session_state.autenticado = True
                st.session_state.usuario = usuario
                st.session_state.rol = usuario["rol"]
                st.session_state.nombre = usuario["nom_res"]
                st.success(f"✅ Bienvenido, {usuario['nom_res']}!")

                if usuario["rol"] == "admin":
                    st.switch_page("pages/admin_dashboard.py")
                else:
                    st.switch_page("pages/trabajador_panel.py")
            else:
                st.error("❌ Correo o contraseña incorrectos")

    st.write("---")
    st.info("Si no tienes cuenta, solicita acceso al administrador.")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            <small>Proyecto Dashboard © 2026 | Sistema de Gestión de Tareas</small>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    login_page()
