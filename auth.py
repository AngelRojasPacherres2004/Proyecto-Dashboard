import streamlit as st
from config.db import get_connection
from styles.main import get_login_style

# ----------------------------
# AUTENTICACIÓN
# ----------------------------
def autenticar(usuario, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM usuarios
        WHERE usuario=%s AND password=%s AND estado='activo'
    """, (usuario, password))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


# ----------------------------
# LOGIN UI
# ----------------------------
def login():

    # 🎨 estilo login
    st.markdown(get_login_style(), unsafe_allow_html=True)

    st.markdown("""
        <style>
            /* Limpia el contenedor para que no se vea blanco ni con sombras raras */
            .stTextInput div[data-baseweb="input"] {
                background-color: #040728c4 !important;
                border: 1px solid rgba(255,255,255,0.2) !important;
                box-shadow: none !important;
            }
            /* Aplica el color solicitado al input interno y asegura el texto blanco */
            .stTextInput input {
                background-color: #040728c4 !important;
                color: white !important;
                -webkit-text-fill-color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    col_card, col_hero = st.columns([0.95, 1.05], gap="large")

    # ===== HERO IZQUIERDO =====
    with col_hero:
        st.markdown("""
            <div class="login-hero">
                <div style="background:rgba(255, 201, 126, 0.14); color:#ffd8a5; padding:0.4rem 1rem; border-radius:20px; display:inline-block; font-size:0.8rem; font-weight:800; margin-bottom:1rem;">SYSTEM OS // v2.0</div>
                <h1 class="login-title">Gestión de Tareas</h1>
                <p style="color:rgba(255,255,255,0.8); margin-bottom:2rem;">Acceso centralizado para el control operativo y seguimiento de tareas en tiempo real.</p>
                <div class="login-point"><strong>Seguimiento centralizado</strong><br>Tareas y responsables en un solo lugar.</div>
                <div class="login-point"><strong>Acceso por roles</strong><br>Vistas optimizadas para cada usuario.</div>
                <div class="login-point"><strong>Diseño de alto rendimiento</strong><br>Interfaz limpia y rápida.</div>
            </div>
        """, unsafe_allow_html=True)

    # ===== FORM LOGIN =====
    with col_card:
        with st.form("login_form"):
            st.markdown('<div style="background:rgba(255, 201, 126, 0.14); color:#ffd8a5; padding:0.4rem 1rem; border-radius:20px; display:inline-block; font-size:0.8rem; font-weight:800; margin-bottom:1rem;">INICIAR SESIÓN</div>', unsafe_allow_html=True)
            st.markdown('<h2 style="color:white; font-weight:900; margin-top:0;">Bienvenido</h2>', unsafe_allow_html=True)
            
            usuario = st.text_input("Usuario", placeholder="Usuario", label_visibility="collapsed")
            password = st.text_input("Contraseña", type="password", placeholder="Contraseña", label_visibility="collapsed")
            
            st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
            submit = st.form_submit_button("Entrar al Sistema", use_container_width=True)
            
            st.markdown("""
                <div style="margin-top:2rem; padding:1rem; border-radius:12px; background:rgba(255,255,255,0.05); font-size:0.85rem; color:#f6e9d7;">
                    Solicita tus credenciales al administrador si no tienes acceso.
                </div>
            """, unsafe_allow_html=True)

        if submit:
            user = autenticar(usuario, password)
            if user:
                st.session_state["user"] = user
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.markdown("</div>", unsafe_allow_html=True)
