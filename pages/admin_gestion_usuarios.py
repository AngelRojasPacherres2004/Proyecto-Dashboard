import streamlit as st
st.sidebar.markdown("### Navegación")
st.sidebar.button("Dashboard", on_click=lambda: st.switch_page("pages/dashboardadmin_gestion_usuarios.py"))