import streamlit as st
from streamlit_option_menu import option_menu

def admin_sidebar(user):

    with st.sidebar:

        # ================= HEADER =================
        st.markdown("""
        <div style="
            text-align:center;
            padding:18px 0;
            border-bottom:1px solid rgba(255,255,255,0.08);
            margin-bottom:18px;
            
        ">
            <div style="font-size:38px;">🚀</div>
            <h2 style="
                color:#f6c27d;
                font-size:16px;
                margin:0;
                font-weight:800;
                letter-spacing:1px;
            ">
                SISTEMA
            </h2>
            <p style="
                color:rgba(255,255,255,0.55);
                font-size:11px;
                margin-top:4px;
                letter-spacing:2px;
            ">
                RENDIMIENTO
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ================= USER CARD =================
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
            padding: 14px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 20px;
            color: white;
        ">
            👨‍💼 <b>{user.get('alias', 'Admin')}</b><br>
            <span style="font-size:11px; color:rgba(255,255,255,0.6);">
                Administrador
            </span>
        </div>
        """, unsafe_allow_html=True)

        # ================= MENU =================
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Usuarios"],
            icons=["speedometer", "people"],
            default_index=0,
            styles={
                "container": {
                    "padding": "0px",
                    "background": "transparent",
                },
                "icon": {
                    "color": "#f6c27d",
                    "font-size": "16px"
                },
                "nav-link": {
                    "color": "white",
                    "text-align": "left",
                    "margin": "4px 0",
                    "border-radius": "12px",
                    "padding": "10px 12px",
                    "transition": "0.2s",
                },
                "nav-link-selected": {
                    "background": "rgba(246, 194, 125, 0.18)",
                    "color": "#ffd18e",
                    "border-left": "3px solid #f6c27d",
                    "font-weight": "700",
                },
            }
        )

        # ================= LOGOUT =================
        st.markdown("<hr style='border:1px solid rgba(255,255,255,0.08)'>", unsafe_allow_html=True)

        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    return selected