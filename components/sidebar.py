import streamlit as st


def admin_sidebar(user):

    with st.sidebar:

        # ================= HEADER =================
        st.markdown(f"""
        <div class="sb-header">
            <div class="sb-logo">⚡</div>
            <div class="sb-name">Sistema</div>
            <div class="sb-role">{user.get('alias', 'Admin')} · Admin</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ================= MENU =================
        opciones = {
            "Dashboard": "📊",
            "Usuarios":  "👥",
            "Empresas":  "🏢",
            "Asignaciones": "📋",
        }

        if "menu_activo" not in st.session_state:
            st.session_state.menu_activo = "Dashboard"

        for nombre, icono in opciones.items():
            activo = st.session_state.menu_activo == nombre
            if st.button(
                f"{icono}  {nombre}",
                key=f"menu_{nombre}",
                use_container_width=True,
                type="primary" if activo else "secondary",
            ):
                st.session_state.menu_activo = nombre
                st.rerun()

        st.markdown("---")

        # ================= LOGOUT =================
        if st.button("🚪  Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    return st.session_state.menu_activo


def trabajador_sidebar(user):
    """Muestra el sidebar con acciones rápidas para el rol de trabajador."""
    if "trabajador_menu" not in st.session_state:
        st.session_state.trabajador_menu = "Reportes"

    with st.sidebar:
        st.markdown(f"""
            <div class="sb-header">
                <div class="sb-logo">👷‍♂️</div>
                <div class="sb-name">Acciones Rápidas</div>
                <div class="sb-role">Funciones comunes</div>
            </div>
        """, unsafe_allow_html=True)

        # Navegación
        if st.button("📊 Ver Reportes", use_container_width=True, key="sb_reports", 
                     type="primary" if st.session_state.trabajador_menu == "Reportes" else "secondary"):
            st.session_state.trabajador_menu = "Reportes"
            st.rerun()

        if st.button("📝 Nueva Tarea", use_container_width=True, key="sb_task",
                     type="primary" if st.session_state.trabajador_menu == "Registro" else "secondary"):
            st.session_state.trabajador_menu = "Registro"
            st.rerun()

        if st.button("👤 Mi Perfil", use_container_width=True, key="sb_profile"):
            st.info("Funcionalidad próximamente")

        st.markdown('---')

        if st.button("🚪 Cerrar Sesión", use_container_width=True, key="sb_logout", type="primary"):
            st.session_state.clear()
            st.rerun()

    return st.session_state.trabajador_menu