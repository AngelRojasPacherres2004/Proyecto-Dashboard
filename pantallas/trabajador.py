import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from components.ui import page_header, section_header, metric_card
from styles.main import get_global_style

def trabajador_home():
    # ================= ESTILO =================
    st.markdown(get_global_style(), unsafe_allow_html=True)

    user = st.session_state.get("user", {})

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
                    <button style="
                        background: rgba(246, 194, 125, 0.1);
                        border: 1px solid #f6c27d;
                        color: #ffd18e;
                        padding: 6px 12px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 12px;
                        transition: all 0.2s;
                    " onmouseover="this.style.background='rgba(246, 194, 125, 0.2)'" onmouseout="this.style.background='rgba(246, 194, 125, 0.1)'">
                        Ver detalles
                    </button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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

    # ================= ACCIONES RÁPIDAS =================
    st.markdown("---")
    section_header("Acciones Rápidas", "Funciones comunes", "⚡")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Nueva Tarea", use_container_width=True):
            st.info("Funcionalidad próximamente")

    with col2:
        if st.button("📊 Ver Reportes", use_container_width=True):
            st.info("Funcionalidad próximamente")

    with col3:
        if st.button("👤 Mi Perfil", use_container_width=True):
            st.info("Funcionalidad próximamente")

    with col4:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()