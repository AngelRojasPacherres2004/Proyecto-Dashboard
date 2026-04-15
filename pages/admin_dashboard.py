import streamlit as st

# ✅ SIEMPRE primero
st.set_page_config(page_title="Admin", layout="wide")

# 🔐 Verificación de login
if not st.session_state.get("autenticado"):
    st.switch_page("pages/login.py")

# 🧠 Página actual
pagina_actual = "dashboard"  # 👈 cambia esto en cada archivo

# 🎨 Estilos sidebar
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        background-color: #111827;
        padding-top: 20px;
    }

    .menu-btn {
        display: block;
        padding: 10px;
        margin: 5px 0;
        border-radius: 8px;
        text-decoration: none;
        color: white;
        background-color: #1f2937;
        text-align: left;
    }

    .menu-btn:hover {
        background-color: #374151;
    }

    .active {
        background-color: #2563eb !important;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 🧱 UI principal
st.title(f"🛠️ Panel Admin — {st.session_state.get('nombre')}")

if st.button("Cerrar sesión"):
    st.session_state.clear()
    st.switch_page("pages/login.py")

# 📚 Sidebar
st.sidebar.markdown("## 📊 Panel Admin")

def menu_item(label, page, key):
    active_class = "active" if pagina_actual == key else ""
    if st.sidebar.button(label, key=key):
        st.switch_page(page)

# 👇 Menú
menu_item("🏠 Dashboard", "pages/admin_dashboard.py", "dashboard")
menu_item("👥 Gestión Usuarios", "pages/admin_gestion_usuarios.py", "usuarios")
menu_item("📝 Gestión Tareas", "pages/admin_gestion_tareas.py", "tareas")
menu_item("🏢 Gestión Empresas", "pages/admin_gestion_empresas.py", "empresas")