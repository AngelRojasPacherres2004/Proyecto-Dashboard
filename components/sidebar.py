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