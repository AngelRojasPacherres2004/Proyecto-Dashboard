import streamlit as st

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
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 14% 18%, rgba(255, 196, 126, 0.32), transparent 22%),
            radial-gradient(circle at 88% 12%, rgba(68, 176, 213, 0.26), transparent 25%),
            linear-gradient(180deg, #fbf4ea 0%, #eef5f8 52%, #edf2f5 100%);
    }
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    .shell {
        max-width: 1120px;
        margin: 0 auto;
        padding: 1.05rem 1rem 2.5rem;
    }
    .hero {
        border-radius: 30px;
        padding: 1.8rem;
        color: #f7fbff;
        background:
            linear-gradient(135deg, rgba(15, 39, 63, 0.98), rgba(13, 111, 120, 0.92)),
            linear-gradient(90deg, #0f273f, #0d6f78);
        box-shadow: 0 24px 54px rgba(25, 48, 67, 0.18);
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: "";
        position: absolute;
        width: 280px;
        height: 280px;
        right: -80px;
        top: -120px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.08);
    }
    .badge {
        display: inline-block;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.14);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 0.95rem;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 900;
        line-height: 1.02;
        letter-spacing: -0.04em;
        max-width: 720px;
        margin-bottom: 0.65rem;
    }
    .hero-copy {
        max-width: 700px;
        line-height: 1.65;
        font-size: 1rem;
        opacity: 0.93;
    }
    .top-actions {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.9rem;
        margin-bottom: 1rem;
    }
    .metrics {
        display: grid;
        grid-template-columns: 1.3fr 0.8fr 0.8fr;
        gap: 1rem;
        margin: 1.2rem 0 1.35rem;
    }
    .metric {
        border-radius: 22px;
        padding: 1rem 1.1rem;
        background: rgba(255, 255, 255, 0.74);
        border: 1px solid rgba(103, 130, 146, 0.16);
        backdrop-filter: blur(10px);
        box-shadow: 0 16px 30px rgba(43, 61, 74, 0.08);
    }
    .metric-label {
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #617989;
        margin-bottom: 0.28rem;
    }
    .metric-value {
        font-size: 1.02rem;
        font-weight: 800;
        color: #173a4f;
    }
    .form-shell {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid rgba(112, 137, 152, 0.16);
        border-radius: 30px;
        padding: 1.55rem;
        box-shadow: 0 24px 40px rgba(44, 63, 75, 0.08);
    }
    .form-heading {
        font-size: 1.18rem;
        font-weight: 900;
        color: #18384a;
        margin-bottom: 0.2rem;
    }
    .form-copy {
        color: #657f8e;
        margin-bottom: 1.2rem;
    }
    .field-card {
        border-radius: 24px;
        padding: 0.85rem 0.95rem;
        background: linear-gradient(180deg, #fbfdff 0%, #f2f8fb 100%);
        border: 1px solid #d9e4eb;
        margin-bottom: 1rem;
    }
    .field-label {
        font-size: 0.79rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #355468;
        margin-bottom: 0.42rem;
    }
    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stSelectbox div[data-baseweb="select"] > div {
        min-height: 3.1rem !important;
        background: white !important;
        border: 1px solid #d3dfe7 !important;
        border-radius: 16px !important;
        box-shadow: none !important;
    }
    .stButton button,
    .stForm button {
        min-height: 3.05rem !important;
        border-radius: 16px !important;
        font-weight: 800 !important;
    }
    .stForm [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #ef7d57 0%, #d8574e 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 16px 28px rgba(216, 87, 78, 0.24);
    }
    @media (max-width: 900px) {
        .metrics {
            grid-template-columns: 1fr;
        }
        .hero-title {
            font-size: 1.9rem;
        }
        .top-actions {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="shell">', unsafe_allow_html=True)

st.markdown('<div class="top-actions">', unsafe_allow_html=True)
left_action, right_action = st.columns(2)
with left_action:
    if st.button("← Retroceder", use_container_width=True):
        st.switch_page("app.py")
with right_action:
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/login.py")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
        <div class="badge">REGISTRO OPERATIVO</div>
        <div class="hero-title">Un formulario más moderno para registrar avances</div>
        <div class="hero-copy">
            Completa la información del proyecto, tarea y fechas clave. Los campos de fecha usan calendario visual para que el ingreso sea más cómodo y preciso.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="metrics">
        <div class="metric">
            <div class="metric-label">TRABAJADOR</div>
            <div class="metric-value">{st.session_state.get('nombre')}</div>
        </div>
        <div class="metric">
            <div class="metric-label">ROL</div>
            <div class="metric-value">{st.session_state.get('rol', 'trabajador')}</div>
        </div>
        <div class="metric">
            <div class="metric-label">ESTADO</div>
            <div class="metric-value">Formulario activo</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="form-shell">', unsafe_allow_html=True)
st.markdown('<div class="form-heading">Formulario de Registro</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="form-copy">Los datos se guardarán en MySQL al presionar el botón de registro.</div>',
    unsafe_allow_html=True,
)

with st.form("registro_trabajador_form"):
    left, right = st.columns(2)

    with left:
        st.markdown('<div class="field-card"><div class="field-label">AÑO</div>', unsafe_allow_html=True)
        anio = st.number_input("AÑO", min_value=2000, max_value=2100, value=2026, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="field-card"><div class="field-label">EMPRESA</div>', unsafe_allow_html=True)
        empresa = st.text_input("EMPRESA", placeholder="Nombre de la empresa", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="field-card"><div class="field-label">PROYECTO</div>', unsafe_allow_html=True)
        proyecto = st.text_input("PROYECTO", placeholder="Nombre del proyecto", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="field-card"><div class="field-label">TAREA</div>', unsafe_allow_html=True)
        tarea = st.text_input("TAREA", placeholder="Describe la tarea", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="field-card"><div class="field-label">MES T</div>', unsafe_allow_html=True)
        mes_t = st.text_input("MES T", placeholder="Ejemplo: Abril", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="field-card"><div class="field-label">ENCARGADO</div>', unsafe_allow_html=True)
        encargado = st.text_input("ENCARGADO", placeholder="Nombre del encargado", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="field-card"><div class="field-label">FECHA REALIZADA</div>', unsafe_allow_html=True)
        fecha_realizada = st.date_input("FECHA REALIZADA", format="YYYY-MM-DD", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="field-card"><div class="field-label">FECHA META</div>', unsafe_allow_html=True)
        fecha_meta = st.date_input("FECHA META", format="YYYY-MM-DD", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="field-card"><div class="field-label">CANTIDAD</div>', unsafe_allow_html=True)
        cantidad = st.number_input("CANTIDAD", min_value=0, step=1, value=0, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="field-card"><div class="field-label">PRIORIDAD</div>', unsafe_allow_html=True)
        prioridad = st.selectbox("PRIORIDAD", ["", "Alta", "Media", "Baja"], label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    submit = st.form_submit_button("Guardar registro", use_container_width=True)

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
