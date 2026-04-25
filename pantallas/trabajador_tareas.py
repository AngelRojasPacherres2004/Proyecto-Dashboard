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
            a.estado,
            e.razon_social as empresa
        FROM asignaciones a
        JOIN tareas t ON a.tarea_id = t.id
        JOIN empresas e ON a.empresa_id = e.id
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
        JOIN empresas e ON a.empresa_id = e.id
        JOIN tareas t ON a.tarea_id = t.id
        JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.id = %s
    """, (asignacion_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def _update_progreso_tarea(asignacion_id, nuevo_estado):
    """Actualiza el estado de la tarea en la base de datos."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE asignaciones 
        SET estado = %s 
        WHERE id = %s
    """, (nuevo_estado, asignacion_id))
    conn.commit()
    cur.close(); conn.close()

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
            st.text_input("📅 AÑO", value=str(detalle['anio']), disabled=True)
            st.text_input("🏢 EMPRESA", value=detalle['empresa'], disabled=True)
            st.text_input("📋 TAREA", value=detalle['tarea'], disabled=True)
            
        with col2:
            st.text_input("🗓️ MES", value=str(detalle['mes']).upper(), disabled=True)
            st.text_input("� ENCARGADO", value=detalle['encargado'], disabled=True)
            estado_opciones = ["pendiente", "en progreso", "completada"]
            nuevo_estado = st.selectbox("🔄 ACTUALIZAR ESTADO", estado_opciones, 
                                      index=estado_opciones.index(detalle['estado'].lower()) if detalle['estado'].lower() in estado_opciones else 0)

        c_meta, c_cant = st.columns(2)
        with c_meta:
            st.text_input("🎯 FECHA META", value=detalle['fecha_meta'].strftime("%d/%m/%Y"), disabled=True)
        with c_cant:
            st.date_input("✅ FECHA REALIZADA", value=datetime.now())

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                _update_progreso_tarea(detalle['id'], nuevo_estado)
                st.success("Progreso guardado.")
        
        with btn_col2:
            if st.button("🔙 Volver al Listado", use_container_width=True):
                st.session_state.vista_actual = "listado"
                st.rerun()

    # Estilo adicional para los inputs deshabilitados (lectura)
    st.markdown("""
        <style>
            div[data-baseweb="input"] input:disabled {
                -webkit-text-fill-color: #f6c27d !important;
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