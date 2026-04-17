import streamlit as st

st.set_page_config(page_title="Tareas", layout="wide")

if not st.session_state.get("autenticado"):
    st.switch_page("login.py")

pagina_actual = "tareas"

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500&family=Syne:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    background-color: #080808;
    color: #e5e5e5;
    font-family: 'Syne', sans-serif;
}

section[data-testid="stSidebar"] {
    background-color: #0d0d0d;
    border-right: 1px solid #1a1a1a;
    min-width: 220px !important;
    max-width: 220px !important;
}

section[data-testid="stSidebar"] > div { padding: 24px 16px; }

.app-logo {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 3px;
    color: #ffffff;
    text-transform: uppercase;
    margin-bottom: 28px;
    padding-bottom: 16px;
    border-bottom: 1px solid #1a1a1a;
}

.user-box {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #ffffff;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 28px;
}

.user-avatar {
    width: 26px;
    height: 26px;
    background: #1a1a1a;
    border: 1px solid #262626;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    color: #ffffff;
    flex-shrink: 0;
}

.sidebar-section {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #ffff;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
    margin-top: 4px;
    padding-left: 4px;
}

div.stButton > button {
    width: 100%;
    background: transparent;
    color: #ffff;
    border: none;
    padding: 8px 10px;
    text-align: left !important;
    border-radius: 5px;
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 400;
    letter-spacing: 0.2px;
    transition: all 0.15s ease;
    display: flex;
    justify-content: flex-start;
}

div.stButton > button:hover {
    background-color: #1a1a1a;
    color: #ffffff;
}

div.stButton > button:focus {
    box-shadow: none;
    border: none;
    outline: none;
}

.btn-active > div > button {
    background-color: #161616 !important;
    color: #e5e5e5 !important;
    border-left: 2px solid #404040 !important;
    border-radius: 0 5px 5px 0 !important;
}

.sidebar-divider {
    height: 1px;
    background: #1a1a1a;
    margin: 16px 0;
}

.logout-btn > div > button {
    color: #3d3d3d !important;
    font-size: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.logout-btn > div > button:hover {
    background-color: #0f0f0f !important;
    color: #7f7f7f !important;
}

h1 {
    color: #ffffff;
    font-family: 'Syne', sans-serif;
    font-weight: 500;
    font-size: 22px;
    letter-spacing: -0.5px;
    margin: 0;
}

.stCaption {
    color: #404040 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
}

.page-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #333;
    letter-spacing: 2px;
}

.tbl-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #383838;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding-bottom: 6px;
}

.tbl-divider {
    height: 1px;
    background: #1a1a1a;
    margin: 4px 0 12px;
}

.task-title {
    font-size: 14px;
    font-weight: 500;
    color: #e5e5e5;
}

.task-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #404040;
    margin-top: 2px;
}

.badge-pendiente {
    background: #1a1500;
    color: #facc15;
    border: 1px solid #713f12;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}

.badge-completada {
    background: #0f2e1a;
    color: #4ade80;
    border: 1px solid #166534;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}

.badge-proceso {
    background: #0f1e2e;
    color: #60a5fa;
    border: 1px solid #1e3a5f;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}

.badge-cancelada {
    background: #1a1010;
    color: #f87171;
    border: 1px solid #7f1d1d;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] div {
    background-color: #111 !important;
    border-color: #1f1f1f !important;
    color: #e5e5e5 !important;
    font-family: 'Syne', sans-serif !important;
    border-radius: 5px !important;
}

label { color: #555 !important; font-size: 12px !important; }

div[data-testid="stExpander"] {
    background: #0d0d0d;
    border: 1px solid #1a1a1a !important;
    border-radius: 6px;
}

[data-testid="stSidebarNav"] { display: none; }

/* Responsive sidebar */
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        min-width: 180px !important;
        max-width: 180px !important;
    }
}

</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="app-logo">⬡ &nbsp;ADMIN</div>', unsafe_allow_html=True)

    nombre_usuario = st.session_state.get("nombre", "admin")
    inicial = nombre_usuario[0].upper() if nombre_usuario else "A"
    st.markdown(f"""
        <div class="user-box">
            <div class="user-avatar">{inicial}</div>
            {nombre_usuario}
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Principal</div>', unsafe_allow_html=True)

    menu_items = [
        ("◈  Dashboard",  "pages/admin_dashboard.py",        "dashboard"),
        ("◎  Usuarios",   "pages/admin_gestion_usuarios.py", "usuarios"),
        ("◷  Tareas",     "pages/admin_gestion_tareas.py",   "tareas"),
        ("◻  Empresas",   "pages/admin_gestion_empresas.py", "empresas"),
    ]

    for label, page, key in menu_items:
        is_active = pagina_actual == key
        if is_active:
            st.markdown('<div class="btn-active">', unsafe_allow_html=True)
        if st.button(label, key=key):
            st.switch_page(page)
        if is_active:
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("→  cerrar sesión", key="logout"):
        st.session_state.clear()
        st.switch_page("login.py")
    st.markdown('</div>', unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────
col_t, col_b = st.columns([6, 1])
with col_t:
    st.markdown('<div style="display:flex;align-items:baseline;gap:12px"><h1>Tareas</h1><span class="page-tag">GESTIÓN</span></div>', unsafe_allow_html=True)
    st.caption("→ 5 registros")

with col_b:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("＋  Nueva")

st.markdown("<br>", unsafe_allow_html=True)

# ─── TABLA MOCK ──────────────────────────────────────────────
tareas_mock = [
    {"titulo": "Migración de base de datos",  "asignado": "Carlos R.",   "empresa": "Tech Solutions SAC",   "vence": "20/04/2026", "estado": "proceso"},
    {"titulo": "Auditoría de seguridad",       "asignado": "María L.",    "empresa": "Inversiones Lima SRL", "vence": "25/04/2026", "estado": "pendiente"},
    {"titulo": "Integración API pagos",        "asignado": "Juan P.",     "empresa": "Tech Solutions SAC",   "vence": "18/04/2026", "estado": "completada"},
    {"titulo": "Reporte mensual Q1",           "asignado": "Ana T.",      "empresa": "Grupo Norte EIRL",     "vence": "15/04/2026", "estado": "completada"},
    {"titulo": "Actualización de servidores",  "asignado": "Luis M.",     "empresa": "Comercial Sur SA",     "vence": "30/04/2026", "estado": "cancelada"},
]

badge_map = {
    "pendiente":  "badge-pendiente",
    "proceso":    "badge-proceso",
    "completada": "badge-completada",
    "cancelada":  "badge-cancelada",
}

# Cabecera
h = st.columns([3, 2, 3, 2, 2, 1, 1])
for col, label in zip(h, ["Tarea", "Asignado", "Empresa", "Vence", "Estado", "", ""]):
    col.markdown(f'<div class="tbl-header">{label}</div>', unsafe_allow_html=True)

st.markdown('<div class="tbl-divider"></div>', unsafe_allow_html=True)

# Filas
for i, t in enumerate(tareas_mock):
    cols = st.columns([3, 2, 3, 2, 2, 1, 1])

    cols[0].markdown(f'<div class="task-title">{t["titulo"]}</div>', unsafe_allow_html=True)
    cols[1].markdown(f'<div class="task-sub">{t["asignado"]}</div>', unsafe_allow_html=True)
    cols[2].markdown(f'<div class="task-sub">{t["empresa"]}</div>', unsafe_allow_html=True)
    cols[3].markdown(f'<div class="task-sub">{t["vence"]}</div>', unsafe_allow_html=True)

    badge = badge_map.get(t["estado"], "badge-pendiente")
    cols[4].markdown(f'<span class="{badge}">{t["estado"]}</span>', unsafe_allow_html=True)

    with cols[5]:
        st.button("✎", key=f"edit_{i}")
    with cols[6]:
        st.button("✕", key=f"del_{i}")

    st.markdown('<div style="height:1px;background:#111;margin:2px 0"></div>', unsafe_allow_html=True)