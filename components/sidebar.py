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
    with st.sidebar:
        st.markdown(f"""
            <div class="sb-header">
                <div class="sb-logo">👷‍♂️</div>
                <div class="sb-name">Acciones Rápidas</div>
                <div class="sb-role">Funciones comunes</div>
            </div>
        """, unsafe_allow_html=True)

        if "menu_trabajador" not in st.session_state:
            st.session_state.menu_trabajador = "Inicio"

        if st.button("🏠 Dashboard", use_container_width=True, key="sb_home", 
                     type="primary" if st.session_state.menu_trabajador == "Inicio" else "secondary"):
            st.session_state.menu_trabajador = "Inicio"
            st.rerun()

        if st.button("👤 Mi Perfil", use_container_width=True, key="sb_profile",
                     type="primary" if st.session_state.menu_trabajador == "Perfil" else "secondary"):
            st.session_state.menu_trabajador = "Perfil"
            st.rerun()

        st.markdown("---")

        

        st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)

        if st.button("🚪 Cerrar Sesión", use_container_width=True, key="sb_logout", type="primary"):
            st.session_state.clear()
            st.rerun()