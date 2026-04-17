import streamlit as st
from utils.sidebar import render_sidebar

# ✅ Configuración
st.set_page_config(page_title="Usuarios", layout="wide")

# 🔐 Verificación de login
if not st.session_state.get("autenticado"):
    st.markdown('<style>section[data-testid="stSidebar"] { display: none !important; }</style>', unsafe_allow_html=True)
    st.switch_page("login.py")

pagina_actual = "usuarios"
render_sidebar("usuarios")

# 🎨 Estilos de la página
st.markdown("""
<style>
h1 {
    color: #e5e5e5;
    font-weight: 500;
        font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 22px;
    letter-spacing: -0.5px;
}
.stCaption {
    color: #404040 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
}
</style>
""", unsafe_allow_html=True)

# 🧱 CONTENIDO PRINCIPAL
st.title("Gestión de Usuarios")
st.caption(f"→ {st.session_state.get('nombre', 'admin')}")

# 🧠 CONTENIDO (puedes mejorar esto luego con tabla real)
st.subheader("Listado de usuarios")
st.info("Aquí puedes mostrar tu tabla de usuarios desde la base de datos.")