import streamlit as st

# ✅ Configuración Pro (Debe ser lo primero)
st.set_page_config(page_title="Admin Panel", layout="wide", initial_sidebar_state="expanded")

# 🔐 Verificación de login
if not st.session_state.get("autenticado"):
    st.switch_page("pages/login.py")

# 🔍 Detectar página actual para iluminar el botón
# (Streamlit no da el path fácilmente, así que usamos un state o el nombre del archivo)
if "pagina_activa" not in st.session_state:
    st.session_state.pagina_activa = "dashboard"

# 🎨 Estilos DARK PREMIUM (Dynamic & Responsive)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400&display=swap');

    :root {
        --bg-dark: #050505;
        --sidebar-bg: #0a0a0a;
        --accent-color: #ffffff;
        --border-color: #1a1a1a;
        --text-muted: #666666;
    }

    /* Fondo general */
    .stApp {
        background-color: var(--bg-dark);
    }

    /* Sidebar Estilizada */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-color);
        transition: all 0.3s ease;
    }

    /* Contenedor de botones para simular 'Active State' */
    .nav-container {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    /* Estilo de botones de navegación */
    div.stButton > button {
        width: 100%;
        background-color: transparent;
        color: var(--text-muted);
        border: 1px solid transparent;
        padding: 10px 15px;
        text-align: left !important;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
    }

    /* Hover dinámico */
    div.stButton > button:hover {
        background-color: #111111;
        color: var(--accent-color);
        border-color: #222;
        transform: translateX(4px);
    }

    /* Botón Activo (basado en lógica de Python) */
    .stButton.active-nav > button {
        background-color: #161616 !important;
        color: white !important;
        border-left: 2px solid white !important;
        font-weight: 600;
    }

    /* Responsividad para móviles */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            min-width: 100vw !important;
            z-index: 9999;
        }
        h1 { font-size: 1.5rem !important; }
    }

    /* Logo y Avatar */
    .app-logo {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        letter-spacing: 4px;
        color: var(--text-muted);
        margin-bottom: 40px;
        padding: 0 10px;
    }

    .user-card {
        background: #0f0f0f;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Ocultar elementos nativos innecesarios */
    [data-testid="stSidebarNav"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# 📚 SIDEBAR DINÁMICA
with st.sidebar:
    st.markdown('<div class="app-logo">SYSTEM_OS v2.0</div>', unsafe_allow_html=True)

    # User Card
    nombre_user = st.session_state.get("nombre", "Admin")
    st.markdown(f"""
        <div class="user-card">
            <div style="width: 32px; height: 32px; background: #222; border-radius: 50%; display: grid; place-items: center; font-size: 12px;">
                {nombre_user[0].upper()}
            </div>
            <div style="font-size: 13px; font-weight: 500;">{nombre_user}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size: 9px; color: #444; letter-spacing: 2px; text-transform: uppercase; margin-left: 10px;">Menú Principal</p>', unsafe_allow_html=True)

    # Diccionario de navegación
    paginas = {
        "dashboard": ("◈  Dashboard", "pages/admin_dashboard.py"),
        "usuarios": ("◎  Usuarios", "pages/admin_gestion_usuarios.py"),
        "tareas": ("◷  Tareas", "pages/admin_gestion_tareas.py"),
        "empresas": ("◻  Empresas", "pages/admin_gestion_empresas.py")
    }

    # Renderizado de botones con detección de estado activo
    for key, (label, path) in paginas.items():
        is_active = st.session_state.pagina_activa == key
        css_class = "active-nav" if is_active else ""
        
        # Usamos un contenedor div para inyectar la clase CSS de 'activo'
        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
        if st.button(label, key=f"btn_{key}"):
            st.session_state.pagina_activa = key
            st.switch_page(path)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 30px; border-top: 1px solid #1a1a1a; padding-top: 20px;"></div>', unsafe_allow_html=True)
    
    # Logout con estilo diferenciado
    if st.button("✕  Cerrar Sesión", key="logout_btn"):
        st.session_state.autenticado = False
        st.switch_page("pages/login.py")

# 🧱 CONTENIDO PRINCIPAL (Dashboard)
# Aquí puedes usar columnas para hacerlo más responsive
col1, col2 = st.columns([2, 1])

with col1:
    st.title("Panel Admin")
    st.caption(f"Gestión de sistemas activo para {nombre_user}")

with col2:
    # Un pequeño widget dinámico para rellenar espacio
    st.markdown("""
    <div style="background: #0f0f0f; padding: 15px; border-radius: 10px; border: 1px solid #1a1a1a; margin-top: 25px;">
        <p style="margin:0; font-size: 10px; color: #666;">ESTADO DEL SERVIDOR</p>
        <p style="margin:0; font-size: 14px; color: #00ff88;">● Online</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()