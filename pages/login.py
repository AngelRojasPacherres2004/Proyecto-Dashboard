import streamlit as st
from services.usuarios_services import autenticar_usuario


def init_session_state():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario = None


def main_app():
    """Aplicación principal después del login"""
    
    with st.sidebar:
        st.write("---")
        st.subheader(f"👤 {st.session_state.usuario['nombre']}")
        st.caption(f"@{st.session_state.usuario['username']}")
        st.caption(f"Rol: {st.session_state.usuario['rol'].capitalize()}")
        
        st.write("---")
        menu = st.radio(
            "📎 Menú",
            ["📊 Dashboard", "📝 Mis Tareas", "📈 Rendimiento", "👥 Admin"]
            if st.session_state.usuario["rol"] == "admin"
            else ["📊 Dashboard", "📝 Mis Tareas", "📈 Rendimiento"],
            label_visibility="collapsed"
        )
        
        st.write("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.usuario = None
            st.rerun()

    if menu == "📊 Dashboard":
        st.title("📊 Dashboard")
        st.write(f"Bienvenido, {st.session_state.usuario['nombre']}!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tareas Totales", "12", "+2 esta semana")
        with col2:
            st.metric("Tareas Completadas", "8", "+1 hoy")
        with col3:
            st.metric("Porcentaje Completado", "66.7%", "+5.3%")
        
        st.divider()
        st.subheader("📋 Actividad Reciente")
        st.info("Tu actividad aparecerá aquí")

    elif menu == "📝 Mis Tareas":
        st.title("📝 Mis Tareas")
        tab1, tab2, tab3 = st.tabs(["Pendientes", "En Progreso", "Completadas"])
        
        with tab1:
            st.write("No tienes tareas pendientes")
        with tab2:
            st.write("No tienes tareas en progreso")
        with tab3:
            st.write("No has completado tareas aún")
        
        st.divider()
        with st.expander("➕ Crear Nueva Tarea"):
            col1, col2 = st.columns(2)
            with col1:
                titulo = st.text_input("Título de la tarea")
            with col2:
                fecha_vencimiento = st.date_input("Fecha de vencimiento")
            descripcion = st.text_area("Descripción")
            if st.button("Crear Tarea"):
                st.success("✅ Tarea creada correctamente")

    elif menu == "📈 Rendimiento":
        st.title("📈 Mi Rendimiento")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Productividad", "75%", "+10%")
            st.metric("Tareas Esta Semana", "5")
        with col2:
            st.metric("Tiempo Promedio", "2.5 horas")
            st.metric("Racha Actual", "3 días")
        st.divider()
        st.subheader("Gráficos de Rendimiento")
        st.info("Los gráficos de rendimiento aparecerán aquí")

    elif menu == "👥 Admin":
        st.title("👥 Panel de Administración")
        tab1, tab2 = st.tabs(["Usuarios", "Configuración"])
        with tab1:
            st.subheader("Gestión de Usuarios")
            st.info("Aquí podrás administrar todos los usuarios del sistema")
        with tab2:
            st.subheader("Configuración del Sistema")
            st.info("Opciones de configuración general")


def login_page():
    """Página de login"""
    
    st.set_page_config(page_title="Login - Dashboard", layout="centered")
    init_session_state()

    if st.session_state.autenticado:
        main_app()
        return

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
