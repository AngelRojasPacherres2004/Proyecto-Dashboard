import streamlit as st
from utils.sidebar import render_sidebar

# ✅ Configuración de página
st.set_page_config(page_title="Panel de Administración", layout="wide", initial_sidebar_state="expanded")

# 🔐 Verificación de login y ocultar sidebar si no está autenticado
if not st.session_state.get("autenticado"):
    st.markdown('<style>section[data-testid="stSidebar"] { display: none !important; }</style>', unsafe_allow_html=True)
    st.switch_page("login.py")

if "pagina_activa" not in st.session_state:
    st.session_state.pagina_activa = "dashboard"

pagina_actual = "dashboard"

# 📚 Sidebar solo si está autenticado
if st.session_state.get("autenticado"):
    render_sidebar("dashboard")

# 🎨 Estilos del Contenido Principal
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&family=JetBrains+Mono:wght@400&display=swap');

    :root {
        --accent-gold: #f6c27d;
        --text-main: #ffffff;
        --border-color: rgba(255, 255, 255, 0.1);
    }

    /* Fondo general */
    .stApp {
        background: radial-gradient(circle at top right, #1a1c25, #08090e);
        color: var(--text-main);
    }

    /* Estilo del Título Principal */
    h1 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800 !important;
        letter-spacing: -0.04em;
        color: white;
        margin-bottom: 0.5rem;
    }

    .metric-card {
        background: rgba(255,255,255,0.03); 
        padding: 25px; 
        border-radius: 24px; 
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        background: rgba(255,255,255,0.06);
        border-color: var(--accent-gold);
        transform: translateY(-4px);
    }

    .metric-label { color: var(--accent-gold); font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; }
    .metric-value { color: white; font-size: 2.2rem; font-weight: 800; margin: 0; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 🧱 CONTENIDO PRINCIPAL
nombre_user = st.session_state.get("nombre", "Admin")
st.markdown(f"""
    <div style="margin-bottom:2.5rem; margin-top: 1rem;">
        <h1 style="font-size:2.5rem;">Panel de Control</h1>
        <p style="color:#f6c27d; font-weight:600; margin-top:5px; opacity:0.9; font-size:1.1rem;">Bienvenido de vuelta, {nombre_user}.</p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# Métricas Principales
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown('<div class="metric-card"><div class="metric-label">USUARIOS TOTALES</div><div class="metric-value">1,240</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-card"><div class="metric-label">TAREAS ACTIVAS</div><div class="metric-value">854</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><div class="metric-label">EMPRESAS</div><div class="metric-value">42</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info("Selecciona una opción del menú lateral para gestionar el sistema.")