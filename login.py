import streamlit as st
import base64
from pathlib import Path
from config.BD_Client import get_connection
from utils.auth import verify_password

# ⚡ Configuración inicial
st.set_page_config(
    page_title="Dashboard - Inicio de Sesión",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🔐 Redirección instantánea si ya está autenticado (Fuera de la función para máxima velocidad)
if st.session_state.get("autenticado"):
    if st.session_state.get("rol") == "admin":
        st.switch_page("pages/admin_dashboard.py")
    else:
        st.switch_page("pages/trabajador_registro.py")

# 🚀 Optimización: Caché para la imagen de fondo

@st.cache_data
def get_base64_background():
    # Ajustamos el path para buscar en la carpeta pages si ahí está la imagen
    fondo_path = Path(__file__).parent / "pages" / "fondo login.png" 
    if fondo_path.exists():
        return base64.b64encode(fondo_path.read_bytes()).decode("utf-8")
    return ""

def login_responsable(usuario_input: str, contrasena: str):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nom_res, alias, usuario, password, rol, estado FROM usuarios WHERE usuario = %s LIMIT 1",
            (usuario_input,),
        )
        usuario = cursor.fetchone()

        if usuario and usuario["estado"] == "activo" and verify_password(contrasena, usuario["password"]):
            return usuario
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def login_page():
    # 🔐 Redirección instantánea dentro de la función para mayor velocidad
    if st.session_state.get("autenticado"):
        if st.session_state.get("rol") == "admin":
            st.switch_page("pages/admin_dashboard.py")
        else:
            st.switch_page("pages/trabajador_registro.py")

    fondo_b64 = get_base64_background()

    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(8, 9, 14, 0.42), rgba(8, 9, 14, 0.58)), url("data:image/png;base64,{fondo_b64}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        [data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
        .login-shell {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1rem; }}
        .login-hero {{ 
            height: 600px; padding: 3rem 2.2rem; border-radius: 32px; 
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(10px); color: #f4efe8;
        }}
        .login-title {{ font-size: 3.2rem; font-weight: 900; letter-spacing: -0.05em; margin-bottom: 1rem; }}
        .login-point {{ padding: 0.8rem; border-radius: 14px; background: rgba(255,255,255,0.04); margin-bottom: 0.5rem; font-size: 0.9rem; }}
        
        [data-testid="stForm"] {{
            border: none !important; background: rgba(255, 255, 255, 0.09) !important;
            border-radius: 32px !important; padding: 2rem !important; backdrop-filter: blur(18px) !important;
            box-shadow: 0 24px 60px rgba(0,0,0,0.34) !important; height: 600px;
        }}
        .stTextInput input {{
            min-height: 3rem !important; background: rgba(255,255,255,0.1) !important;
            color: white !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.1) !important;
        }}
        .stForm [data-testid="stFormSubmitButton"] button {{
            min-height: 3.2rem !important; border-radius: 14px !important; font-weight: 800 !important;
            background: linear-gradient(135deg, #ffd18e 0%, #f0a84f 100%) !important; color: #1d1611 !important; border: none;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    col_hero, col_card = st.columns([1.05, 0.95], gap="large")

    with col_hero:
        st.markdown("""
            <div class="login-hero">
                <div style="background:rgba(255, 201, 126, 0.14); color:#ffd8a5; padding:0.4rem 1rem; border-radius:20px; display:inline-block; font-size:0.8rem; font-weight:800; margin-bottom:1rem;">SYSTEM OS // v2.0</div>
                <h1 class="login-title">Gestión de Proyectos</h1>
                <p style="color:rgba(255,255,255,0.8); margin-bottom:2rem;">Acceso centralizado para el control operativo y seguimiento de tareas en tiempo real.</p>
                <div class="login-point"><strong>Seguimiento centralizado</strong><br>Tareas y responsables en un solo lugar.</div>
                <div class="login-point"><strong>Acceso por roles</strong><br>Vistas optimizadas para cada usuario.</div>
                <div class="login-point"><strong>Diseño de alto rendimiento</strong><br>Interfaz limpia y rápida.</div>
            </div>
        """, unsafe_allow_html=True)

    with col_card:
        with st.form("login_form"):
            st.markdown('<div style="font-size:0.8rem; font-weight:800; color:#f6c27d;">INICIAR SESIÓN</div>', unsafe_allow_html=True)
            st.markdown('<h2 style="color:white; font-weight:900; margin-top:0;">Bienvenido</h2>', unsafe_allow_html=True)
            
            usuario_input = st.text_input("Usuario", placeholder="Usuario", label_visibility="collapsed")
            password = st.text_input("Contraseña", type="password", placeholder="Contraseña", label_visibility="collapsed")
            
            st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
            submit_login = st.form_submit_button("Entrar al Sistema", use_container_width=True)
            
            st.markdown("""
                <div style="margin-top:2rem; padding:1rem; border-radius:12px; background:rgba(255,255,255,0.05); font-size:0.85rem; color:#f6e9d7;">
                    Solicita tus credenciales al administrador si no tienes acceso.
                </div>
            """, unsafe_allow_html=True)

        if submit_login:
            if not usuario_input or not password:
                st.error("Campos vacíos")
            else:
                usuario = login_responsable(usuario_input, password)
                if usuario:
                    st.session_state.autenticado = True
                    st.session_state.rol = usuario["rol"]
                    st.session_state.nombre = usuario["nom_res"]
                    st.session_state.usuario = usuario
                    st.rerun() # ⚡ Rerun para ejecutar la redirección al inicio del archivo
                else:
                    st.error("Credenciales inválidas")

    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    login_page()
