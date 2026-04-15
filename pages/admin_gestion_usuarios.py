import streamlit as st

# ✅ Configuración
st.set_page_config(page_title="Usuarios", layout="wide")

# 🔐 Verificación de login
if not st.session_state.get("autenticado"):
    st.switch_page("pages/login.py")

pagina_actual = "usuarios"

import streamlit as st

# ✅ Configuración
st.set_page_config(page_title="Usuarios", layout="wide")

# 🔐 Verificación de login
if not st.session_state.get("autenticado"):
    st.switch_page("pages/login.py")

pagina_actual = "usuarios"

# 🎨 Estilos DARK MINIMAL
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500&family=Syne:wght@400;500;600&display=swap');

/* Fondo */
html, body, [class*="css"] {
    background-color: #080808;
    color: #ffff;
    font-family: 'Syne', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0d0d0d;
    border-right: 1px solid #1a1a1a;
    min-width: 220px !important;
    max-width: 220px !important;
}

section[data-testid="stSidebar"] > div {
    padding: 24px 16px;
}

/* Logo / App name */
.app-logo {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 3px;
    color: #ffff;
    text-transform: uppercase;
    margin-bottom: 28px;
    padding-bottom: 16px;
    border-bottom: 1px solid #1a1a1a;
}

/* Usuario */
.user-box {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #ffff;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 28px;
}

.user-avatar {
    width: 26px;
    height: 26px;
    background: #1a1a1a;
    border: 1px solid #262626;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    color: #ffff;
    flex-shrink: 0;
}

/* Sección label */
.sidebar-section {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #ffff;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
    margin-top: 4px;
    padding-left: 4px;
}

/* Botones del menú */
div.stButton > button {
    width: 100%;
    background: transparent;
    color: #ffff;
    border: none;
    padding: 8px 10px;
    text-align: left !important;
    border-radius: 5px;
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 400;
    letter-spacing: 0.2px;
    transition: all 0.15s ease;
    display: flex;
    justify-content: flex-start;
}

div.stButton > button:hover {
    background-color: #1a1a1a;
    color: #ffff;
}

div.stButton > button:focus {
    box-shadow: none;
    border: none;
    outline: none;
}

/* Botón activo */
.btn-active > div > button {
    background-color: #161616 !important;
    color: #e5e5e5 !important;
    border-left: 2px solid #404040 !important;
    border-radius: 0 5px 5px 0 !important;
}

/* Separador */
.sidebar-divider {
    height: 1px;
    background: #1a1a1a;
    margin: 16px 0;
}

/* Logout */
.logout-btn > div > button {
    color: #3d3d3d !important;
    font-size: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.logout-btn > div > button:hover {
    background-color: #0f0ff !important;
    color: #7f7f7f !important;
}

/* Título principal */
h1 {
    color: #e5e5e5;
    font-weight: 500;
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    letter-spacing: -0.5px;
}

.stCaption {
    color: #404040 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
}

/* Ocultar decoración por defecto de Streamlit en sidebar */
.st-emotion-cache-1cypcdb, [data-testid="stSidebarNav"] {
    display: none;
}

/* Responsive sidebar */
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        min-width: 180px !important;
        max-width: 180px !important;
    }
}

</style>
""", unsafe_allow_html=True)

# 🧱 CONTENIDO PRINCIPAL
st.title("Gestión de Usuarios")
st.caption(f"→ {st.session_state.get('nombre', 'admin')}")

# 📚 SIDEBAR
with st.sidebar:

    # App name
    st.markdown('<div class="app-logo">⬡ &nbsp;ADMIN</div>', unsafe_allow_html=True)

    # 👤 Usuario
    nombre = st.session_state.get("nombre", "admin")
    inicial = nombre[0].upper() if nombre else "A"
    st.markdown(f"""
        <div class="user-box">
            <div class="user-avatar">{inicial}</div>
            {nombre}
        </div>
    """, unsafe_allow_html=True)

    # 📌 Sección: Principal
    st.markdown('<div class="sidebar-section">Principal</div>', unsafe_allow_html=True)

    # Menú con iconos
    menu_items = [
        ("◈  Dashboard",  "pages/admin_dashboard.py",         "dashboard"),
        ("◎  Usuarios",   "pages/admin_gestion_usuarios.py",  "usuarios"),
        ("◷  Tareas",     "pages/admin_gestion_tareas.py",    "tareas"),
        ("◻  Empresas",   "pages/admin_gestion_empresas.py",  "empresas"),
    ]

    for label, page, key in menu_items:
        is_active = pagina_actual == key
        if is_active:
            st.markdown('<div class="btn-active">', unsafe_allow_html=True)
        if st.button(label, key=key):
            st.switch_page(page)
        if is_active:
            st.markdown('</div>', unsafe_allow_html=True)

    # Separador
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # 🔐 Logout
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("→  cerrar sesión", key="logout"):
        st.session_state.clear()
        st.switch_page("pages/login.py")
    st.markdown('</div>', unsafe_allow_html=True)

# 🧠 CONTENIDO (puedes mejorar esto luego con tabla real)
st.subheader("Listado de usuarios")
st.info("Aquí puedes mostrar tu tabla de usuarios desde la base de datos.")