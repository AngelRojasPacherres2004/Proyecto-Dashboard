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
            radial-gradient(circle at top left, rgba(167, 214, 255, 0.45), transparent 28%),
            radial-gradient(circle at bottom right, rgba(14, 91, 128, 0.18), transparent 26%),
            linear-gradient(180deg, #f4f8fb 0%, #edf3f7 100%);
    }
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    .worker-wrap {
        max-width: 980px;
        margin: 0 auto;
        padding: 1.2rem 1rem 2.5rem;
    }
    .hero-shell {
        border-radius: 28px;
        padding: 1.4rem 1.5rem 1.2rem;
        background: linear-gradient(135deg, rgba(10, 91, 128, 0.96), rgba(49, 125, 160, 0.9));
        box-shadow: 0 22px 45px rgba(26, 54, 74, 0.16);
        color: white;
        margin-bottom: 1.25rem;
    }
    .hero-kicker {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.14);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 0.85rem;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: -0.03em;
        margin-bottom: 0.45rem;
    }
    .hero-subtitle {
        font-size: 1rem;
        line-height: 1.55;
        max-width: 680px;
        opacity: 0.92;
    }
    .toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin: 1rem 0 1.25rem;
        padding: 1rem 1.1rem;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.76);
        border: 1px solid rgba(120, 151, 173, 0.22);
        backdrop-filter: blur(10px);
    }
    .worker-card {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(120, 151, 173, 0.22);
        border-radius: 28px;
        padding: 1.7rem 1.4rem;
        box-shadow: 0 18px 36px rgba(40, 63, 81, 0.08);
    }
    .worker-label {
        text-align: right;
        color: #0a5b80;
        font-size: 1rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        padding-top: 0.55rem;
    }
    .section-heading {
        color: #21465d;
        font-size: 1.05rem;
        font-weight: 800;
        margin: 0 0 1rem 0;
        padding-left: 0.2rem;
    }
    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stSelectbox div[data-baseweb="select"] > div {
        min-height: 3rem !important;
        background: #f7fbfd !important;
        border: 1px solid #d5e3ec !important;
        border-radius: 18px !important;
        box-shadow: none !important;
    }
    .stButton button, .stForm button {
        border-radius: 16px !important;
        font-weight: 700 !important;
    }
    .stForm [data-testid="stFormSubmitButton"] button {
        min-height: 3rem !important;
        background: linear-gradient(135deg, #0f6e98 0%, #1295a8 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 14px 26px rgba(18, 149, 168, 0.22);
    }
    @media (max-width: 768px) {
        .worker-wrap {
            padding: 0.8rem 0.5rem 2rem;
        }
        .hero-title {
            font-size: 1.65rem;
        }
        .worker-label {
            text-align: left;
            padding-top: 0.1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

top_left, top_right = st.columns([5, 1])
with top_left:
    st.markdown(
        """
        <div class="hero-shell">
            <div class="hero-kicker">PANEL DEL TRABAJADOR</div>
            <div class="hero-title">Formulario de Registro</div>
            <div class="hero-subtitle">
                Registra avances, tareas y fechas clave en un formato claro y ordenado para el seguimiento del proyecto.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top_right:
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.switch_page("pages/login.py")

st.markdown('<div class="worker-wrap">', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="toolbar">
        <div><strong>Trabajador:</strong> {st.session_state.get('nombre')}</div>
        <div><strong>Estado:</strong> Listo para registrar</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="worker-card">', unsafe_allow_html=True)

with st.form("registro_trabajador_form"):
    st.markdown('<div class="section-heading">Datos del registro</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">AÑO</div>', unsafe_allow_html=True)
    with c2:
        anio = st.number_input("AÑO", min_value=2000, max_value=2100, value=2026, label_visibility="collapsed")

    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">EMPRESA</div>', unsafe_allow_html=True)
    with c2:
        empresa = st.text_input("EMPRESA", placeholder="Ingresa la empresa", label_visibility="collapsed")

    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">PROYECTO</div>', unsafe_allow_html=True)
    with c2:
        proyecto = st.text_input("PROYECTO", placeholder="Ingresa el proyecto", label_visibility="collapsed")

    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">TAREA</div>', unsafe_allow_html=True)
    with c2:
        tarea = st.text_input("TAREA", placeholder="Ingresa la tarea", label_visibility="collapsed")

    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">MES T</div>', unsafe_allow_html=True)
    with c2:
        mes_t = st.text_input("MES T", placeholder="Ingresa el mes", label_visibility="collapsed")

    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">ENCARGADO</div>', unsafe_allow_html=True)
    with c2:
        encargado = st.text_input("ENCARGADO", placeholder="Ingresa el encargado", label_visibility="collapsed")

    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">FECHA REALIZADA</div>', unsafe_allow_html=True)
    with c2:
        fecha_realizada = st.date_input("FECHA REALIZADA", format="YYYY-MM-DD", label_visibility="collapsed")

    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">FECHA META</div>', unsafe_allow_html=True)
    with c2:
        fecha_meta = st.date_input("FECHA META", format="YYYY-MM-DD", label_visibility="collapsed")

    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">CANT</div>', unsafe_allow_html=True)
    with c2:
        cantidad = st.number_input("CANT", min_value=0, step=1, value=0, label_visibility="collapsed")

    c1, c2 = st.columns([1.1, 1.6])
    with c1:
        st.markdown('<div class="worker-label">PRIORIDAD</div>', unsafe_allow_html=True)
    with c2:
        prioridad = st.selectbox("PRIORIDAD", ["", "Alta", "Media", "Baja"], label_visibility="collapsed")

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
