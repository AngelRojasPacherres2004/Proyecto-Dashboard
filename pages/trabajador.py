import streamlit as st

def trabajador_home():

    st.title("👷 Panel Trabajador")

    st.write(f"Bienvenido: {st.session_state['user']['alias']}")

    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()