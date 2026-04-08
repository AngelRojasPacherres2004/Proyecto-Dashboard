import streamlit as st
from services.usuarios_services import autenticar_usuario


def login_page():
    """Página de login"""
    
    st.set_page_config(page_title="Login - Dashboard", layout="centered")

    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario = None

    # CSS personalizado
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
        username = st.text_input(
            "👤 Nombre de usuario",
            placeholder="Ingresa tu nombre de usuario"
        )
        password = st.text_input(
            "🔑 Contraseña",
            type="password",
            placeholder="Ingresa tu contraseña"
        )
        submit_login = st.form_submit_button("Iniciar Sesión", use_container_width=True)

    if submit_login:
        if not username or not password:
            st.error("⚠️ Por favor completa todos los campos")
        else:
            with st.spinner("Verificando credenciales..."):
                resultado = autenticar_usuario(username, password)
            if resultado["exito"]:
                st.session_state.autenticado = True
                st.session_state.usuario = resultado["usuario"]
                st.success(f"✅ {resultado['mensaje']}")
                st.info(f"Bienvenido, {resultado['usuario']['nombre']}!")
                st.rerun()
            else:
                st.error(f"❌ {resultado['mensaje']}")

    st.write("---")
    st.info(
        "Si no tienes cuenta aún, obtén tus credenciales desde Supabase o solicita acceso al administrador."
    )
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            <small>Proyecto Dashboard © 2026 | Sistema de Gestión de Tareas</small>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    login_page()
