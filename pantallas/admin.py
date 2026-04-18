import streamlit as st
from styles.main import get_admin_style
from components.sidebar import admin_sidebar


def admin_home():

    # ================= ESTILO GLOBAL =================
    st.markdown(get_admin_style(), unsafe_allow_html=True)

    # ================= USER =================
    user = st.session_state.get("user", {})

    # ================= SIDEBAR =================
    opcion = admin_sidebar(user)

    # ================= HEADER CONTENIDO =================
    st.markdown(f"""
        <div style="margin-bottom:25px;">
            <h1 style="margin-bottom:5px;">Panel Admin</h1>
            <p style="color:rgba(255,255,255,0.6); margin:0;">
                Bienvenido, {user.get('alias', 'Admin')}
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ================= ROUTING =================
    if opcion == "Dashboard":

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">ESTADO</div>
                <div class="metric-value">ACTIVO</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">USUARIOS</div>
                <div class="metric-value">120</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">TAREAS</div>
                <div class="metric-value">85</div>
            </div>
            """, unsafe_allow_html=True)

    elif opcion == "Usuarios":

        st.markdown("""
        <div style="margin-bottom:15px;">
            <h2 style="margin:0;">Gestión de usuarios</h2>
            <p style="color:rgba(255,255,255,0.6); margin-top:5px;">
                Administra los usuarios del sistema
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.info("Aquí luego haces el CRUD")