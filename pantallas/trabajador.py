import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from components.ui import page_header, section_header, metric_card
from components.sidebar import trabajador_sidebar
from styles.main import get_admin_style
from pantallas.trabajador_perfil import trabajador_perfil
from pantallas.trabajador_tareas import vista_detalle_tarea, render_nueva_tarea_placeholder

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

    # ================= MÉTRICAS PERSONALES =================
    section_header("Mi Rendimiento", "Tus estadísticas del mes actual", "📊")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Tareas Hoy", "8", "✅")

    with col2:
        metric_card("Tareas Semana", "42", "📅")

    with col3:
        metric_card("Eficiencia", "91%", "🎯")

    with col4:
        metric_card("Puntuación", "4.7", "⭐")

    st.markdown("---")

    # ================= TAREAS PENDIENTES =================
    section_header("Tareas Pendientes", "Actividades que requieren tu atención", "📋")

    # Tareas de ejemplo
    tareas_pendientes = [
        {
            "titulo": "Revisar documentación del proyecto Alpha",
            "prioridad": "Alta",
            "fecha_limite": (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y"),
            "estado": "En progreso"
        },
        {
            "titulo": "Actualizar base de datos de clientes",
            "prioridad": "Media",
            "fecha_limite": (datetime.now() + timedelta(days=5)).strftime("%d/%m/%Y"),
            "estado": "Pendiente"
        },
        {
            "titulo": "Preparar reporte mensual",
            "prioridad": "Baja",
            "fecha_limite": (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y"),
            "estado": "Pendiente"
        }
    ]

    for tarea in tareas_pendientes:
        prioridad_color = {"Alta": "#ff6b6b", "Media": "#ffd93d", "Baja": "#6bcf7f"}.get(tarea["prioridad"], "#6bcf7f")
        estado_icono = {"Pendiente": "⏳", "En progreso": "🔄", "Completada": "✅"}.get(tarea["estado"], "⏳")

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
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 16px; margin-right: 8px;">{estado_icono}</span>
                        <h4 style="color: white; margin: 0; font-size: 16px; font-weight: 600;">{tarea['titulo']}</h4>
                    </div>
                    <div style="display: flex; gap: 16px; font-size: 14px;">
                        <span style="color: {prioridad_color};">🔥 {tarea['prioridad']}</span>
                        <span style="color: rgba(255,255,255,0.7);">📅 {tarea['fecha_limite']}</span>
                        <span style="color: rgba(255,255,255,0.7);">{tarea['estado']}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Botón funcional de Streamlit para "Ver detalles"
        if st.button(f"🔎 Ver detalles: {tarea['titulo']}", key=f"btn_det_{tarea['titulo']}"):
            st.session_state.tarea_seleccionada_id = 1 # Aquí usarías el ID real de la BD
            st.session_state.vista_actual = "detalle"
            st.rerun()

    st.markdown("---")

    # ================= ACTIVIDAD RECIENTE =================
    section_header("Actividad Reciente", "Tu historial de las últimas 24 horas", "🕒")

    actividades = [
        {"accion": "Completaste tarea: 'Actualizar perfil de usuario'", "hora": "Hace 2 horas", "tipo": "completada"},
        {"accion": "Iniciaste sesión en el sistema", "hora": "Hace 8 horas", "tipo": "login"},
        {"accion": "Actualizaste tu información personal", "hora": "Hace 1 día", "tipo": "perfil"}
    ]

    for actividad in actividades:
        icono = {"completada": "✅", "login": "🔑", "perfil": "👤"}.get(actividad["tipo"], "📝")
        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.02);
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            border: 1px solid rgba(255,255,255,0.05);
        ">
            <span style="font-size: 16px; margin-right: 12px;">{icono}</span>
            <div style="flex: 1; color: rgba(255,255,255,0.9);">
                {actividad['accion']}
            </div>
            <span style="color: rgba(255,255,255,0.5); font-size: 12px;">{actividad['hora']}</span>
        </div>
        """, unsafe_allow_html=True)