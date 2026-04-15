import streamlit as st

from config.BD_Client import get_connection

if not st.session_state.get("autenticado"):
    st.switch_page("pages/login.py")

st.markdown(
    """
    <style>
    .worker-wrap {
        max-width: 920px;
        margin: 0 auto;
        padding: 0.75rem 1rem 2rem;
    }
    .worker-banner {
        width: 100%;
        background: linear-gradient(90deg, #d9ecfb 0%, #c7dff3 100%);
        color: #2f3441;
        text-align: center;
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        padding: 0.3rem 1rem;
        margin: 1rem 0 1.75rem;
    }
    .worker-card {
        background: #efefef;
        padding: 1.5rem 1.25rem;
    }
    .worker-label {
        text-align: right;
        color: #0a5b80;
        font-size: 1.05rem;
        font-weight: 800;
        padding-top: 0.35rem;
    }
    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stSelectbox div[data-baseweb="select"] > div {
        background: #f9fafb !important;
        border-radius: 18px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="worker-wrap">', unsafe_allow_html=True)
st.markdown('<div class="worker-banner">FORMULARIO DE REGISTRO</div>', unsafe_allow_html=True)
st.markdown('<div class="worker-card">', unsafe_allow_html=True)

with st.form("registro_trabajador_form"):
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

st.set_page_config(page_title="Mi Panel", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title(f"👷 Mi Panel — {st.session_state.get('nombre')}")

if st.button("Cerrar sesión"):
    st.session_state.clear()
    st.switch_page("pages/login.py")
