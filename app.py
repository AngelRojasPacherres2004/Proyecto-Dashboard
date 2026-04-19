import streamlit as st
from auth import login
from pantallas.admin_dashboard import admin_home
from pantallas.trabajador import trabajador_home


st.set_page_config(page_title="Sistema", layout="wide")

# estado inicial
if "auth" not in st.session_state:
    st.session_state["auth"] = False

# LOGIN
if not st.session_state["auth"]:
    login()
    st.stop()

user = st.session_state["user"]
rol = user["rol"]

# RUTEO POR ROL
if rol == "admin":
    admin_home()

elif rol == "trabajador":
    trabajador_home()