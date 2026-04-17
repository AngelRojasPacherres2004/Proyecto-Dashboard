import streamlit as st
import sys
import base64
from pathlib import Path

from config.BD_Client import get_connection
from utils.auth import verify_password

# Agregar la raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))


def login_responsable(usuario_input: str, contrasena: str):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, nom_res, alias, usuario, password, rol, estado, fecha_creacion
            FROM usuarios
            WHERE usuario = %s
            LIMIT 1
            """,
            (usuario_input,),
        )
        usuario = cursor.fetchone()

        if not usuario or usuario["estado"] != "activo":
            return None

        password_guardado = usuario["password"]

        if verify_password(contrasena, password_guardado):
            return {
                "id": usuario["id"],
                "nom_res": usuario["nom_res"],
                "alias": usuario["alias"],
                "usuario": usuario["usuario"],
                "rol": usuario["rol"],
                "estado": usuario["estado"],
                "fecha_creacion": usuario["fecha_creacion"],
            }
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def login_page():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario = None

    fondo_path = Path(__file__).parent / "fondo login.png"
    fondo_b64 = ""
    if fondo_path.exists():
        fondo_b64 = base64.b64encode(fondo_path.read_bytes()).decode("utf-8")

    css_login = """
        <style>
        .stApp {
            background:
                linear-gradient(rgba(8, 9, 14, 0.42), rgba(8, 9, 14, 0.58)),
                url("data:image/png;base64,__FONDO_B64__");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background:
                linear-gradient(150deg, transparent 8%, rgba(255, 199, 122, 0.24) 12%, transparent 18%),
                linear-gradient(332deg, transparent 76%, rgba(255, 199, 122, 0.2) 81%, transparent 87%);
            opacity: 0.92;
        }
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        [data-testid="stAppViewContainer"] > .main {
            background: transparent !important;
        }
        .login-shell {
            max-width: 1100px;
            margin: 0 auto;
            padding: 2rem 1rem 2.5rem;
        }
        .login-grid {
            display: grid;
            grid-template-columns: 1.05fr 0.95fr;
            gap: 1.4rem;
            align-items: stretch;
        }
        .login-hero {
            height: 630px;
            padding: 3rem 2.2rem;
            border-radius: 32px;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)),
                radial-gradient(circle at 18% 20%, rgba(255, 202, 128, 0.18), transparent 22%);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
            color: #f4efe8;
            backdrop-filter: blur(10px);
        }
        .login-badge {
            display: inline-block;
            padding: 0.38rem 0.9rem;
            border-radius: 999px;
            background: rgba(255, 201, 126, 0.14);
            color: #ffd8a5;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            margin-bottom: 1.15rem;
        }
        .login-title {
            font-size: 3.2rem;
            line-height: 0.98;
            letter-spacing: -0.05em;
            margin: 0 0 1rem 0;
            font-weight: 900;
            max-width: 520px;
        }
        .login-copy {
            max-width: 520px;
            color: rgba(245, 239, 232, 0.82);
            line-height: 1.7;
            font-size: 1.02rem;
        }
        .login-points {
            margin-top: 2rem;
            display: grid;
            gap: 0.85rem;
        }
        .login-point {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.07);
            color: #f6e9d7;
        }
        .login-card {
            height: 630px;
            border-radius: 32px;
            padding: 1.4rem;
            background: rgba(255, 255, 255, 0.09);
            border: 1px solid rgba(255,255,255,0.12);
            box-shadow: 0 24px 60px rgba(0,0,0,0.34);
            backdrop-filter: blur(18px);
        }
        .login-card-inner {
            height: 100%;
            border-radius: 24px;
            padding: 1.4rem 1.3rem 1.2rem;
            background: linear-gradient(180deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            border: 1px solid rgba(255,255,255,0.08);
        }
        .form-eyebrow {
            color: #f6c27d;
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            margin-bottom: 0.55rem;
        }
        .form-title {
            color: #fff8f0;
            font-size: 2rem;
            font-weight: 900;
            letter-spacing: -0.04em;
            margin-bottom: 0.45rem;
        }
        .form-copy {
            color: rgba(255,255,255,0.74);
            margin-bottom: 1.2rem;
            line-height: 1.6;
        }
        .helper-note {
            margin-top: 1rem;
            padding: 0.9rem 1rem;
            border-radius: 16px;
            color: #f7e7cd;
            background: rgba(255, 198, 116, 0.1);
            border: 1px solid rgba(255, 198, 116, 0.16);
            font-size: 0.94rem;
        }
        .login-footer {
            text-align: center;
            color: rgba(255,255,255,0.54);
            margin-top: 1rem;
            font-size: 0.86rem;
        }
        .stTextInput label p {
            color: #f3ecdf !important;
            font-weight: 700;
        }
        .stTextInput input {
            min-height: 3.15rem !important;
            background: rgba(255,255,255,0.1) !important;
            color: #fff7ef !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            border-radius: 16px !important;
        }
        .stTextInput input::placeholder {
            color: rgba(255,255,255,0.45) !important;
        }
        .stForm [data-testid="stFormSubmitButton"] button {
            min-height: 3.1rem !important;
            border-radius: 16px !important;
            font-weight: 800 !important;
            border: none !important;
            color: #1d1611 !important;
            background: linear-gradient(135deg, #ffd18e 0%, #f0a84f 100%) !important;
            box-shadow: 0 18px 28px rgba(240, 168, 79, 0.28);
        }
        [data-testid="stForm"] {
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
            height: 630px;
            border-radius: 32px !important;
            padding: 1.4rem !important;
            background: rgba(255, 255, 255, 0.09) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            box-shadow: 0 24px 60px rgba(0,0,0,0.34) !important;
            backdrop-filter: blur(18px) !important;
        }
        [data-testid="stForm"] > div:first-child {
            padding: 3rem 2.2rem !important;
            background: linear-gradient(180deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 24px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            height: 100% !important;
        }
        div[data-testid="stAlert"] {
            border-radius: 18px !important;
        }
        @media (max-width: 900px) {
            .login-grid {
                grid-template-columns: 1fr;
            }
            .login-hero,
            .login-card {
                min-height: auto;
            }
            .login-title {
                font-size: 2.45rem;
            }
        }
        </style>
        """
    st.markdown(css_login.replace("__FONDO_B64__", fondo_b64), unsafe_allow_html=True)

    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    col_hero, col_card = st.columns([1.05, 0.95], gap="large")

    with col_hero:
        st.markdown(
            """
                <div class="login-hero">
                    <div class="login-badge">PLATAFORMA DE GESTIÓN</div>
                    <h1 class="login-title">Dashboard de Proyectos</h1>
                    <div class="login-copy">
                        Accede a tu espacio de trabajo con una experiencia más elegante, enfocada en claridad, seguimiento y control operativo.
                    </div>
                    <div class="login-points">
                        <div class="login-point"><strong>Seguimiento centralizado</strong><br>Consulta tareas, fechas clave y responsables en un solo lugar.</div>
                        <div class="login-point"><strong>Acceso por roles</strong><br>El sistema adapta la vista para administradores y trabajadores.</div>
                        <div class="login-point"><strong>Diseño limpio</strong><br>Una interfaz más cuidada para trabajar con menos distracción.</div>
                    </div>
                </div>
                """,
            unsafe_allow_html=True,
        )

    with col_card:
        with st.form("login_form"):
            st.markdown(
                """
                <div class="form-eyebrow">INICIAR SESIÓN</div>
                <div class="form-title">Bienvenido de nuevo</div>
                <div class="form-copy">Ingresa tus credenciales para continuar al panel del sistema.</div>
                """,
                unsafe_allow_html=True
            )

            usuario_input = st.text_input("Usuario", placeholder="Ingresa tu usuario", label_visibility="collapsed")
            password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña", label_visibility="collapsed")
            submit_login = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            st.markdown(
            """
            <div class="helper-note">Si no tienes cuenta, solicita acceso al administrador del sistema.</div>
            <div class="login-footer">Proyecto Dashboard © 2026 | Sistema de Gestión de Tareas</div>
            """,
            unsafe_allow_html=True
        )
        if submit_login:
            if not usuario_input or not password:
                st.error("Completa todos los campos.")
            else:
                with st.spinner("Verificando credenciales..."):
                    usuario = login_responsable(usuario_input, password)

                if usuario:
                    st.session_state.autenticado = True
                    st.session_state.usuario = usuario
                    st.session_state.rol = usuario["rol"]
                    st.session_state.nombre = usuario["nom_res"]
                    st.success(f"Bienvenido, {usuario['nom_res']}.")
                    st.switch_page("pages/admin_dashboard.py" if usuario["rol"] == "admin" else "pages/trabajador_registro.py")
                else:
                    st.error("Usuario o contraseña incorrectos.")

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    login_page()