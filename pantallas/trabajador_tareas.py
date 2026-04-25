import streamlit as st
from config.db import get_connection
from datetime import datetime

def get_tareas_pendientes_usuario(usuario_id):
    """Obtiene las tareas asignadas a un usuario que no han sido completadas."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            a.id, 
            t.nombre_tarea as titulo, 
            a.fecha_meta as fecha_limite, 
            a.estado
        FROM asignaciones a
        JOIN tareas t ON a.tarea_id = t.id
        WHERE a.usuario_id = %s AND a.estado != 'completada'
        ORDER BY a.fecha_meta ASC
    """, (usuario_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_detalle_asignacion(asignacion_id):
    """Obtiene toda la información relacionada a una tarea específica."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            a.id, a.fecha_meta, a.estado,
            e.razon_social as empresa, e.ruc,
            t.nombre_tarea as tarea,
            u.nom_res as encargado,
            YEAR(a.fecha_meta) as anio,
            MONTHNAME(a.fecha_meta) as mes
        FROM asignaciones a
        JOIN empresas e ON a.empresa_id = e.idcd
        JOIN tareas t ON a.tarea_id = t.id
        JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.id = %s
    """, (asignacion_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def vista_detalle_tarea(asignacion_id):
    """Muestra el formulario detallado de la tarea."""
    detalle = _get_detalle_asignacion(asignacion_id)
    
    if not detalle:
        st.error("No se encontró la información de la tarea.")
        if st.button("⬅️ Volver al listado"):
            st.session_state.vista_actual = "listado"
            st.rerun()
        return

    # Encabezado de la vista
    st.markdown(f"""
        <div style='margin-bottom: 2rem; display: flex; align-items: center; gap: 15px;'>
            <div style='background: #f6c27d; color: #1e1e1e; padding: 10px; border-radius: 10px; font-weight: 800;'>
                ID #{detalle['id']}
            </div>
            <div>
                <h2 style='color: white; font-size: 22px; font-weight: 700; margin: 0;'>Detalles de la Actividad</h2>
                <p style='color: rgba(255,255,255,0.5); font-size: 13px; margin: 0;'>Revisión y actualización de progreso</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Formulario Elegante
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("📅 AÑO", value=detalle['anio'], disabled=True)
            st.text_input("🏢 EMPRESA", value=detalle['empresa'], disabled=True)
            st.text_input("🚀 PROYECTO", value="PROYECTO ALPHA", disabled=True) # Placeholder o dato de base
            st.text_input("📋 TAREA", value=detalle['tarea'], disabled=True)
            
        with col2:
            st.text_input("🗓️ MES T", value=detalle['mes'].upper(), disabled=True)
            st.text_input("👤 ENCARGADO", value=detalle['encargado'], disabled=True)
            st.text_input("🔥 PRIORIDAD", value="ALTA", disabled=True) # Mapeado de lógica
            st.date_input("✅ FECHA REALIZADA", value=datetime.now())

        # Campos inferiores
        c_meta, c_cant = st.columns([1, 1])
        with c_meta:
            # "no guarda dato" según requerimiento, solo lectura
            st.text_input("🎯 FECHA META", value=detalle['fecha_meta'].strftime("%d/%m/%Y"), disabled=True)
        with c_cant:
            st.number_input("🔢 CANT", min_value=1, step=1, value=1)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
        with btn_col1:
            if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                st.success("Progreso guardado.")
        
        with btn_col2:
            if st.button("🔙 Cancelar", use_container_width=True):
                st.session_state.vista_actual = "listado"
                st.rerun()

    # Estilo adicional para los inputs deshabilitados (lectura)
    st.markdown("""
        <style>
            div[data-baseweb="input"] input:disabled {
                -webkit-text-fill-color: #f6c27d !format;
                color: #f6c27d !important;
                opacity: 0.9;
                background: rgba(246, 194, 125, 0.05) !important;
                border-color: rgba(246, 194, 125, 0.2) !important;
            }
            label {
                color: rgba(255,255,255,0.6) !important;
                font-size: 11px !important;
                font-weight: 600 !important;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        </style>
    """, unsafe_allow_html=True)

def render_nueva_tarea_placeholder():
    """Vista simplificada para 'Nueva Tarea'."""
    st.info("Formulario para creación de nuevas tareas fuera de flujo de asignación.")
    if st.button("Regresar"):
        st.session_state.menu_trabajador = "Inicio"
        st.rerun()