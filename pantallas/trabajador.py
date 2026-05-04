import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from components.ui import page_header, section_header, metric_card
from components.sidebar import trabajador_sidebar
from styles.main import get_admin_style
from pantallas.trabajador_perfil import trabajador_perfil
from pantallas.trabajador_tareas import vista_detalle_tarea, render_nueva_tarea_placeholder, get_tareas_pendientes_usuario

def _badge_estado_tarea(estado: str) -> str:
    """Genera un badge de estado estilizado."""
    cfg = {
        "pendiente":   ("rgba(246,194,125,0.15)", "#f6c27d"),
        "en progreso": ("rgba(133,183,235,0.15)", "#85B7EB"),
        "completada":  ("rgba(93,202,165,0.15)",  "#5DCAA5"),
        "vencida":     ("rgba(240,149,149,0.15)", "#F09595"),
    }
    bg, color = cfg.get(estado.lower(), ("rgba(255,255,255,0.08)", "white"))
    return f'<span style="background:{bg};color:{color};padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;text-transform:uppercase;">{estado}</span>'

def trabajador_home():
    # ================= ESTILO =================
    st.markdown(get_admin_style(), unsafe_allow_html=True)

    user = st.session_state.get("user", {})

    # ================= SIDEBAR (ACCIONES RÁPIDAS) =================
    trabajador_sidebar(user)

    # ================= ROUTING =================
    opcion = st.session_state.get("menu_trabajador", "Inicio")

    if opcion == "Perfil":
        trabajador_perfil()
    elif opcion == "Nueva Tarea":
        render_nueva_tarea_placeholder()
    else:
        # Manejo interno de sub-vistas (Lista o Detalle)
        if "vista_actual" not in st.session_state:
            st.session_state.vista_actual = "listado"
        
        if st.session_state.vista_actual == "detalle":
            vista_detalle_tarea(st.session_state.tarea_seleccionada_id)
        else:
            render_trabajador_dashboard(user)

def render_trabajador_dashboard(user):
    """Contenido principal del panel de trabajador."""
    # ================= HEADER =================
    page_header("Panel de Trabajador", f"Bienvenido, {user.get('alias', 'Trabajador')}")

    # ================= TAREAS PENDIENTES =================
    section_header("Tareas Pendientes", "Actividades actuales", "-")

    # Obtener tareas reales de la base de datos
    tareas_pendientes = get_tareas_pendientes_usuario(user.get("id"))

    if not tareas_pendientes:
        st.info("No tienes tareas pendientes asignadas.")

    # Cabecera de la tabla alineada
    with st.container():
        hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([2.5, 2, 1.5, 1.2, 0.8])
        headers = ["TAREA", "EMPRESA", "FECHA LÍMITE", "ESTADO", "ACCIONES"]
        for col, header in zip([hcol1, hcol2, hcol3, hcol4, hcol5], headers):
            col.markdown(f"<span style='color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;'>{header}</span>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    for tarea in tareas_pendientes:
        estado_icono = {"pendiente": "", "en progreso": "🔄", "completada": "✅"}.get(tarea["estado"].lower(), "⏳")
        fecha_fmt = tarea['fecha_limite'].strftime("%d/%m/%Y") if hasattr(tarea['fecha_limite'], 'strftime') else tarea['fecha_limite']
        
        hoy = datetime.now().date()
        es_vencida = tarea['fecha_limite'] < hoy if hasattr(tarea['fecha_limite'], 'date') else False
        fecha_color = "#F09595" if es_vencida else "white"
        alerta_vencido = " ⚠" if es_vencida else ""
        
        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([2.5, 2, 1.5, 1.2, 0.8])
            
            with col1:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 16px;">{estado_icono}</span>
                        <span style="color:white; font-weight:600; font-size:14px;">{tarea['titulo']}</span>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<span style='color:#85B7EB; font-size:13px; font-weight:500;'> {tarea['empresa']}</span>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"<span style='color:{fecha_color}; font-size:13px;'> {fecha_fmt}{alerta_vencido}</span>", unsafe_allow_html=True)
            
            with col4:
                st.markdown(_badge_estado_tarea(tarea['estado']), unsafe_allow_html=True)
            
            with col5:
                if st.button(" Ver", key=f"btn_det_{tarea['id']}", use_container_width=True):
                    st.session_state.tarea_seleccionada_id = tarea['id']
                    st.session_state.vista_actual = "detalle"
                    st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)