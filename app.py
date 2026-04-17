import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="Dashboard - Gestión de Proyectos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None

from pages.login import login_page

def main():
    if not st.session_state.autenticado:
        login_page()
    else:
        # Si alguien llega aquí ya autenticado, redirigir según rol
        if st.session_state.get("rol") == "admin":
            st.switch_page("pages/admin_dashboard.py")
        else:
            st.switch_page("pages/trabajador_registro.py")

if __name__ == "__main__":
    main()
