import streamlit as st

if not st.session_state.get("autenticado"):
    st.switch_page("pages/login.py")

st.set_page_config(page_title="Mi Panel", layout="wide")
st.title(f"👷 Mi Panel — {st.session_state.get('nombre')}")

if st.button("Cerrar sesión"):
    st.session_state.clear()
    st.switch_page("pages/login.py")