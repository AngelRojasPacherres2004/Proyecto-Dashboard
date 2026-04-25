import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from components.ui import page_header, section_header, metric_card
from components.sidebar import trabajador_sidebar
from styles.main import get_admin_style
from pantallas.trabajador_perfil import trabajador_perfil
from pantallas.trabajador_tareas import vista_detalle_tarea, render_nueva_tarea_placeholder, get_tareas_pendientes_usuario

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
    section_header("Tareas Pendientes", "Actividades actuales", "📋")

    # Obtener tareas reales de la base de datos
    tareas_pendientes = get_tareas_pendientes_usuario(user.get("id"))

    if not tareas_pendientes:
        st.info("No tienes tareas pendientes asignadas.")

    for tarea in tareas_pendientes:
        # Como la prioridad no está en la base de datos aún, usaremos un color por defecto o lógica de fecha
        prioridad_color = "#f6c27d" # Color dorado institucional
        estado_icono = {"Pendiente": "⏳", "En progreso": "🔄", "Completada": "✅"}.get(tarea["estado"], "⏳")
        fecha_fmt = tarea['fecha_limite'].strftime("%d/%m/%Y") if hasattr(tarea['fecha_limite'], 'strftime') else tarea['fecha_limite']

        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.03);
            padding: 16px;
            border-radius: 12px;
            border-left: 4px solid {prioridad_color};
            margin-bottom: 12px;
            transition: all 0.3s ease;
        " onmouseover="this.style.transform='translateX(4px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.2)'"
           onmouseout="this.style.transform='translateX(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.1)'">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 16px; margin-right: 8px;">{estado_icono}</span>
                        <h4 style="color: white; margin: 0; font-size: 16px; font-weight: 600;">{tarea['titulo']}</h4>
                    </div>
                    <div style="display: flex; gap: 16px; font-size: 14px;">
                        <span style="color: rgba(255,255,255,0.7);">{tarea['estado']}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Botón funcional de Streamlit para "Ver detalles"
        if st.button(f"🔎 Ver detalles: {tarea['titulo']}", key=f"btn_det_{tarea['id']}"):
            st.session_state.tarea_seleccionada_id = tarea['id']
            st.session_state.vista_actual = "detalle"
            st.rerun()

    st.markdown("---")