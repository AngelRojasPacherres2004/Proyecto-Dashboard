import streamlit as st
from streamlit_option_menu import option_menu

def admin_home():

    with st.sidebar:
        st.title(f"👨‍💼 Admin: {st.session_state['user']['alias']}")

        opcion = option_menu(
            "Menú",
            ["Dashboard", "Usuarios"],
            icons=["speedometer", "people"],
            default_index=0
        )

        st.markdown("---")

        if st.button("🚪 Cerrar sesión"):
            st.session_state.clear()
            st.rerun()

    # CONTENIDO
    st.title("Panel Admin")

    if opcion == "Dashboard":
        st.subheader("Resumen general")
        st.metric("Estado", "Activo sistema")

    elif opcion == "Usuarios":
        st.subheader("Gestión de usuarios")
        st.write("Aquí luego haces CRUD")