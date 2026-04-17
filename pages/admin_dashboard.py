import streamlit as st

# ✅ Configuración Pro
st.set_page_config(page_title="Admin Panel", layout="wide", initial_sidebar_state="expanded")

# 🔐 Verificación de login
if not st.session_state.get("autenticado"):
    st.switch_page("pages/login.py")

if "pagina_activa" not in st.session_state:
    st.session_state.pagina_activa = "dashboard"

# 🎨 Estilos PREMIUM GOLD & CONTRAST (Inspirado en tu diseño anterior)
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

    /* Fondo general */
    .stApp {
        background: radial-gradient(circle at top right, #1a1c25, #08090e);
        color: var(--text-main);
    }

    /* Sidebar Estilizada con contraste alto */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-color);
        backdrop-filter: blur(15px);
    }

    /* Logo - Mayor contraste */
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

    /* User Card - Más visible */
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

    /* Botones de Navegación - ALTO CONTRASTE */
    div.stButton > button {
        width: 100%;
        background-color: transparent;
        color: #eeeeee !important; /* Texto casi blanco para leer bien */
        border: 1px solid transparent;
        padding: 12px 18px;
        text-align: left !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 15px;
        font-weight: 500;
        border-radius: 12px;
        transition: all 0.3s ease;
    }

    /* Hover con el naranja/oro del diseño anterior */
    div.stButton > button:hover {
        background-color: rgba(246, 194, 125, 0.1) !important;
        color: var(--accent-bright) !important;
        border-color: rgba(246, 194, 125, 0.3);
        transform: translateX(5px);
    }

    /* Botón Activo - Muy visible */
    .active-nav div.stButton > button {
        background: linear-gradient(90deg, rgba(246, 194, 125, 0.2), transparent) !important;
        color: var(--accent-gold) !important;
        border-left: 4px solid var(--accent-gold) !important;
        font-weight: 800 !important;
    }

    /* Estilo del Título Principal */
    h1 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800 !important;
        letter-spacing: -0.04em;
        color: white;
    }

    .stCaption {
        color: var(--text-muted) !important;
        font-size: 1rem;
    }

    /* Ocultar elementos nativos */
    [data-testid="stSidebarNav"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 📚 SIDEBAR DINÁMICA
with st.sidebar:
    st.markdown('<div class="app-logo">SYSTEM_OS // ADMIN</div>', unsafe_allow_html=True)

    # User Card
    nombre_user = st.session_state.get("nombre", "Administrador")
    st.markdown(f"""
        <div class="user-card">
            <div style="width: 38px; height: 38px; background: var(--accent-gold); color: #1d1611; border-radius: 10px; display: grid; place-items: center; font-weight: 800; font-size: 16px;">
                {nombre_user[0].upper()}
            </div>
            <div>
                <div style="font-size: 14px; font-weight: 700; color: white;">{nombre_user}</div>
                <div style="font-size: 11px; color: #f6c27d; font-weight: 600;">Súper Usuario</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size: 10px; color: #666; letter-spacing: 2px; text-transform: uppercase; margin-left: 10px; font-weight:800;">Navegación</p>', unsafe_allow_html=True)

    paginas = {
        "dashboard": ("📊 Dashboard Global", "pages/admin_dashboard.py"),
        "usuarios": ("👤 Gestión Usuarios", "pages/admin_gestion_usuarios.py"),
        "tareas": ("📋 Control de Tareas", "pages/admin_gestion_tareas.py"),
        "empresas": ("🏢 Directorio Empresas", "pages/admin_gestion_empresas.py")
    }

    for key, (label, path) in paginas.items():
        is_active = st.session_state.pagina_activa == key
        # Aplicamos la clase envolvente para el estilo activo
        st.markdown(f'<div class="{"active-nav" if is_active else ""}">', unsafe_allow_html=True)
        if st.button(label, key=f"btn_{key}"):
            st.session_state.pagina_activa = key
            st.switch_page(path)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 30px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 20px;"></div>', unsafe_allow_html=True)
    
    if st.button("Logout ✕", key="logout_btn"):
        st.session_state.clear()
        st.switch_page("pages/login.py")

# 🧱 CONTENIDO PRINCIPAL
col1, col2 = st.columns([3, 1])

with col1:
    st.title("Panel de Administración")
    st.markdown(f"<p style='color:var(--accent-gold); font-weight:600;'>Bienvenido de vuelta, {nombre_user}.</p>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: rgba(0, 255, 136, 0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(0, 255, 136, 0.2); margin-top: 20px; text-align: center;">
        <p style="margin:0; font-size: 10px; color: #00ff88; font-weight:800; letter-spacing:1px;">SISTEMA EN LÍNEA</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Ejemplo de métricas con el nuevo estilo de contraste
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown("""
    <div style="background: rgba(255,255,255,0.03); padding: 20px; border-radius: 20px; border: 1px solid var(--border-color);">
        <p style="color: #f6c27d; font-size: 12px; font-weight: 800; margin-bottom: 5px;">USUARIOS TOTALES</p>
        <h2 style="margin:0; color: white; font-weight: 800;">1,240</h2>
    </div>
    """, unsafe_allow_html=True)
# ... puedes repetir para m2 y m3