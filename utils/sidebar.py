import streamlit as st

def render_sidebar(pagina_actual: str):
    """
    Renderiza la barra lateral personalizada para el panel de administración.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&family=JetBrains+Mono:wght@400&display=swap');

        :root {
            --bg-dark: #08090e;
            --sidebar-bg: rgba(15, 16, 22, 0.95);
            --accent-gold: #f6c27d;
            --accent-bright: #ffd18e;
            --text-main: #ffffff;
            --text-muted: #a0a0a0;
            --border-color: rgba(255, 255, 255, 0.1);
        }

        section[data-testid="stSidebar"] {
            background-color: var(--sidebar-bg) !important;
            border-right: 1px solid var(--border-color);
            backdrop-filter: blur(15px);
        }

        .app-logo {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 3px;
            color: var(--accent-gold);
            margin-bottom: 30px;
            padding: 0 10px;
            opacity: 0.9;
        }

        .user-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="app-logo">SYSTEM_OS // ADMIN</div>', unsafe_allow_html=True)

        nombre_user = st.session_state.get("nombre", "Administrador")
        st.markdown(f"""
            <div class="user-card">
                <div style="width: 38px; height: 38px; background: #f6c27d; color: #1d1611; border-radius: 10px; display: grid; place-items: center; font-weight: 800; font-size: 16px;">
                    {nombre_user[0].upper()}
                </div>
                <div>
                    <div style="font-size: 14px; font-weight: 700; color: white;">{nombre_user}</div>
                    <div style="font-size: 11px; color: #f6c27d; font-weight: 600;">Súper Usuario</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<p style="font-size: 10px; color: #666; letter-spacing: 2px; text-transform: uppercase; margin-left: 10px; font-weight:800;">Navegación</p>', unsafe_allow_html=True)

        menu_items = [
            ("◈  Dashboard",  "pages/admin_dashboard.py",         "dashboard"),
            ("◎  Usuarios",   "pages/admin_gestion_usuarios.py",  "usuarios"),
            ("◷  Tareas",     "pages/admin_gestion_tareas.py",    "tareas"),
            ("◻  Empresas",   "pages/admin_gestion_empresas.py",  "empresas"),
        ]

        for label, page, key in menu_items:
            is_active = pagina_actual == key
            
            # Aplicamos estilo visual si es la página activa
            if is_active:
                st.markdown('<div style="border-left: 3px solid #f6c27d; padding-left: 5px;">', unsafe_allow_html=True)
            
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.switch_page(page)
            
            if is_active:
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-top: 30px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 20px;"></div>', unsafe_allow_html=True)
        
        if st.button("🚪 Cerrar Sesión", key="logout_btn_sidebar", use_container_width=True):
            st.markdown("""
                <style>
                    section[data-testid="stSidebar"], 
                    [data-testid="stSidebarNav"], 
                    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
                </style>
            """, unsafe_allow_html=True)
            st.session_state.clear()
            st.switch_page("login.py")