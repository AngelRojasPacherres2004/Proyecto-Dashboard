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
        estado_icono = {"pendiente": "⏳", "en progreso": "🔄", "completada": "✅"}.get(tarea["estado"].lower(), "⏳")
        fecha_fmt = tarea['fecha_limite'].strftime("%d/%m/%Y") if hasattr(tarea['fecha_limite'], 'strftime') else tarea['fecha_limite']
        
        # Lógica de alerta de fecha
        hoy = datetime.now().date()
        vencida = tarea['fecha_limite'] < hoy if hasattr(tarea['fecha_limite'], 'date') else False
        fecha_color = "#F09595" if vencida else "rgba(255,255,255,0.6)"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
            padding: 22px;
            border-radius: 18px;
            border-left: 6px solid {prioridad_color};
            border-top: 1px solid rgba(255,255,255,0.06);
            border-right: 1px solid rgba(255,255,255,0.03);
            border-bottom: 1px solid rgba(255,255,255,0.06);
            margin-bottom: 18px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        " onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 16px rgba(0,0,0,0.25)'"
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.1)'">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 20px; margin-right: 14px;">{estado_icono}</span>
                        <h4 style="color: white; margin: 0; font-size: 18px; font-weight: 700; letter-spacing: 0.4px;">{tarea['titulo']}</h4>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 18px; font-size: 13px; margin-top: 12px; margin-left: 34px;">
                        <span style="color: #85B7EB; font-weight: 600;">🏢 {tarea['empresa']}</span>
                        <span style="color: {fecha_color}; font-weight: 600;">📅 Límite: {fecha_fmt}</span>
                        <span style="background: rgba(255,255,255,0.08); padding: 3px 11px; border-radius: 7px; color: rgba(255,255,255,0.65); font-size: 10.5px; text-transform: uppercase; font-weight: 700;">
                            {tarea['estado']}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Botón funcional estilizado, ahora más integrado visualmente
        # Usando una columna pequeña para empujar el botón a la derecha, haciéndolo menos "blocky"
        col_spacer, col_button = st.columns([0.8, 0.2])
        with col_button:
            # CSS personalizado para el botón para hacerlo más pequeño y como un icono
            st.markdown(f"""
                <style>
                    div[data-testid="stButton"] > button[key="btn_det_{tarea['id']}"] {{
                        background-color: rgba(246, 194, 125, 0.15);
                        color: #f6c27d;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 18px;
                        border: none;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        transition: all 0.2s ease;
                    }}
                    div[data-testid="stButton"] > button[key="btn_det_{tarea['id']}"]:hover {{
                        background-color: #f6c27d;
                        color: #1e1e1e;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    }}
                </style>
            """, unsafe_allow_html=True)
            if st.button("🔎", key=f"btn_det_{tarea['id']}"): # Texto cambiado a icono
                st.session_state.tarea_seleccionada_id = tarea['id']
                st.session_state.vista_actual = "detalle"
                st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True) # Espaciado reducido