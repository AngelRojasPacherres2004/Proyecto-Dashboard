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

    
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 🎨 estilo login
    st.markdown(get_login_style(), unsafe_allow_html=True)

    # =========================
    # LAYOUT LOGIN
    # =========================
    col_hero, col_card = st.columns([1.05, 0.95], gap="large")

    # ===== HERO IZQUIERDO =====
    with col_hero:
        st.markdown("""
<div style="background:rgba(255, 201, 126, 0.14);
color:#ffd8a5; padding:0.4rem 1rem;
border-radius:20px; display:inline-block;
font-size:0.8rem; font-weight:800;
margin-bottom:1rem;">
SYSTEM OS
</div>

<h1 class="login-title">Gestión de Rendimiento</h1>

<p style="color:rgba(255,255,255,0.75); margin-bottom:2rem;">
Control de tareas y rendimiento por usuario en tiempo real.
</p>

<div class="login-point"><b>📊 Seguimiento</b><br>Monitoreo de tareas</div>
<div class="login-point"><b>👥 Roles</b><br>Admin y trabajadores</div>
<div class="login-point"><b>⚡ Velocidad</b><br>Interfaz optimizada</div>
""", unsafe_allow_html=True)

    # ===== FORM LOGIN =====
    with col_card:

        with st.form("login_form"):

            st.markdown("### Iniciar sesión")

            usuario = st.text_input("Usuario", placeholder="Usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Contraseña")

            submit = st.form_submit_button("Entrar al sistema", use_container_width=True)

        if submit:

            user = autenticar(usuario, password)

            if user:
                st.session_state["user"] = user
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")