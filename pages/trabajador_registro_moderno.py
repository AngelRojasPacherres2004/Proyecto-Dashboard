import streamlit as st
import base64
from pathlib import Path

from config.BD_Client import get_connection


if not st.session_state.get("autenticado"):
    st.switch_page("pages/login.py")


def guardar_registro_trabajador(
    anio,
    empresa,
    proyecto,
    tarea,
    mes_t,
    encargado,
    fecha_realizada,
    fecha_meta,
    cantidad,
    prioridad,
    responsable_id,
):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO registros_trabajador (
                anio, empresa, proyecto, tarea, mes_t, encargado,
                fecha_realizada, fecha_meta, cantidad, prioridad, responsable_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                anio,
                empresa,
                proyecto,
                tarea,
                mes_t,
                encargado,
                fecha_realizada,
                fecha_meta,
                cantidad,
                prioridad,
                responsable_id,
            ),
        )
        conn.commit()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "mensaje": str(exc)}
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


st.set_page_config(page_title="Registro del Trabajador", layout="wide")
fondo_path = Path(__file__).parent / "fondo login.png"
fondo_b64 = ""
if fondo_path.exists():
    fondo_b64 = base64.b64encode(fondo_path.read_bytes()).decode("utf-8")

css_registro = """
    <style>
    .stApp {
        background:
            linear-gradient(rgba(8, 9, 14, 0.45), rgba(8, 9, 14, 0.65)),
            url("data:image/png;base64,__FONDO_B64__");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    .login-shell {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    .login-grid {
        display: grid;
        grid-template-columns: 0.8fr 1.2fr;
        gap: 1.5rem;
        align-items: stretch;
    }
    .login-hero {
        padding: 2.5rem 2.2rem;
        border-radius: 32px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255,255,255,0.08);
        backdrop-filter: blur(12px);
        color: #f4efe8;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .login-badge {
        display: inline-block;
        padding: 0.4rem 0.9rem;
        border-radius: 999px;
        background: rgba(255, 201, 126, 0.14);
        color: #ffd8a5;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 1.2rem;
    }
    .login-title {
        font-size: 2.8rem;
        font-weight: 900;
        line-height: 1.05;
        letter-spacing: -0.04em;
        margin-bottom: 1.2rem;
        color: #fff;
    }
    .metric-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 1.2rem;
        border-radius: 20px;
        margin-bottom: 1rem;
    }
    .metric-label { font-size: 0.72rem; color: #f6c27d; font-weight: 800; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.15rem; color: #fff; font-weight: 700; margin-top: 0.2rem; }

    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.09) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 32px !important;
        padding: 0 !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 24px 60px rgba(0,0,0,0.35) !important;
    }
    [data-testid="stForm"] > div:first-child {
        padding: 2.5rem !important;
        background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)) !important;
        border-radius: 24px !important;
    }
    .field-label {
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #f6c27d;
        margin-bottom: 0.5rem;
        margin-top: 0.8rem;
    }
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {
        min-height: 3rem !important;
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: white !important;
        border-radius: 14px !important;
    }
    .stForm [data-testid="stFormSubmitButton"] button {
        margin-top: 1.5rem;
        min-height: 3.3rem !important;
        background: linear-gradient(135deg, #ffd18e 0%, #f0a84f 100%) !important;
        color: #1d1611 !important;
        font-weight: 800 !important;
        border-radius: 16px !important;
        border: none !important;
        box-shadow: 0 10px 20px rgba(240, 168, 79, 0.2);
    }
    .nav-button button {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #fff !important;
        border-radius: 12px !important;
    }
    @media (max-width: 900px) {
        .login-grid { grid-template-columns: 1fr; }
    }
    </style>
    """
st.markdown(css_registro.replace("__FONDO_B64__", fondo_b64), unsafe_allow_html=True)

st.markdown('<div class="login-shell">', unsafe_allow_html=True)

# Botones de navegación superiores
col_nav1, col_nav2 = st.columns([4, 1])
with col_nav1:
    st.markdown('<div class="nav-button">', unsafe_allow_html=True)
    if st.button("← Inicio"): st.switch_page("app.py")
    st.markdown('</div>', unsafe_allow_html=True)
with col_nav2:
    st.markdown('<div class="nav-button">', unsafe_allow_html=True)
    if st.button("Cerrar Sesión"):
        st.session_state.clear()
        st.switch_page("pages/login.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="login-grid">', unsafe_allow_html=True)

# Columna Izquierda: Hero / Info
with st.container():
    st.markdown(
        f"""
        <div class="login-hero">
            <div>
                <div class="login-badge">REGISTRO OPERATIVO</div>
                <h1 class="login-title">Control de Avances</h1>
                <p style="opacity:0.85; line-height:1.7;">Registra tus actividades diarias con precisión. Toda la información se sincroniza directamente con el panel de administración para seguimiento en tiempo real.</p>
            </div>
            <div>
                <div class="metric-card">
                    <div class="metric-label">TRABAJADOR</div>
                    <div class="metric-value">{st.session_state.get('nombre', 'Usuario')}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">ESTADO DEL SISTEMA</div>
                    <div class="metric-value">✓ Conectado</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Columna Derecha: Formulario
with st.container():
    with st.form("registro_trabajador_form"):
        st.markdown('<div style="color:#fff8f0; font-size:1.8rem; font-weight:900; margin-bottom:0.5rem; letter-spacing:-0.03em;">Detalles de la Tarea</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:rgba(255,255,255,0.7); margin-bottom:1.5rem; font-size:0.95rem;">Ingresa los datos para guardar el registro oficial.</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="field-label">AÑO</div>', unsafe_allow_html=True)
            anio = st.number_input("AÑO", min_value=2000, max_value=2100, value=2026, label_visibility="collapsed")
            
            st.markdown('<div class="field-label">EMPRESA</div>', unsafe_allow_html=True)
            empresa = st.text_input("EMPRESA", placeholder="Nombre de la empresa", label_visibility="collapsed")
            
            st.markdown('<div class="field-label">PROYECTO</div>', unsafe_allow_html=True)
            proyecto = st.text_input("PROYECTO", placeholder="Nombre del proyecto", label_visibility="collapsed")
            
            st.markdown('<div class="field-label">TAREA</div>', unsafe_allow_html=True)
            tarea = st.text_input("TAREA", placeholder="Descripción de la tarea", label_visibility="collapsed")
            
            st.markdown('<div class="field-label">MES</div>', unsafe_allow_html=True)
            mes_t = st.text_input("MES", placeholder="Ej. Abril", label_visibility="collapsed")
        
        with c2:
            st.markdown('<div class="field-label">ENCARGADO</div>', unsafe_allow_html=True)
            encargado = st.text_input("ENCARGADO", placeholder="Persona a cargo", label_visibility="collapsed")
            
            st.markdown('<div class="field-label">FECHA REALIZADA</div>', unsafe_allow_html=True)
            fecha_realizada = st.date_input("FECHA REALIZADA", format="YYYY-MM-DD", label_visibility="collapsed")
            
            st.markdown('<div class="field-label">FECHA META</div>', unsafe_allow_html=True)
            fecha_meta = st.date_input("FECHA META", format="YYYY-MM-DD", label_visibility="collapsed")
            
            st.markdown('<div class="field-label">CANTIDAD</div>', unsafe_allow_html=True)
            cantidad = st.number_input("CANTIDAD", min_value=0, step=1, value=0, label_visibility="collapsed")
            
            st.markdown('<div class="field-label">PRIORIDAD</div>', unsafe_allow_html=True)
            prioridad = st.selectbox("PRIORIDAD", ["", "Alta", "Media", "Baja"], label_visibility="collapsed")

        submit = st.form_submit_button("Guardar Registro en Sistema", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True) # Cierre login-grid
st.markdown("</div>", unsafe_allow_html=True) # Cierre login-shell

if submit:
    obligatorios = [empresa, proyecto, tarea, mes_t, encargado, prioridad]
    if any(not valor for valor in obligatorios):
        st.error("Completa todos los campos obligatorios.")
    else:
        resultado = guardar_registro_trabajador(
            anio=anio,
            empresa=empresa,
            proyecto=proyecto,
            tarea=tarea,
            mes_t=mes_t,
            encargado=encargado,
            fecha_realizada=fecha_realizada,
            fecha_meta=fecha_meta,
            cantidad=cantidad,
            prioridad=prioridad,
            responsable_id=st.session_state.get("usuario", {}).get("id"),
        )
        if resultado["ok"]:
            st.success("Registro guardado correctamente.")
        else:
            st.error(f"No se pudo guardar el registro: {resultado['mensaje']}")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
