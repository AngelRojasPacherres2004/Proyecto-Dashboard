import streamlit as st
from config.db import get_connection
from datetime import datetime, date

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
            MONTHNAME(a.fecha_meta) as mes,
            a.usuario_id, a.tarea_id, a.empresa_id
        FROM asignaciones a
        JOIN empresas e ON a.empresa_id = e.id
        JOIN tareas t ON a.tarea_id = t.id
        JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.id = %s
    """, (asignacion_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def _get_grupo_trabajo(tarea_id, empresa_id, fecha_meta):
    """
    Obtiene todas las asignaciones del mismo grupo (misma tarea, empresa y fecha_meta).
    Retorna lista de tuplas (id, usuario_id) donde id es la referencia principal.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, usuario_id
        FROM asignaciones
        WHERE tarea_id = %s AND empresa_id = %s AND fecha_meta = %s
        ORDER BY id ASC
    """, (tarea_id, empresa_id, fecha_meta))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _calcular_rendimiento(fecha_realizada, fecha_meta):
    """Calcula el rendimiento basado en la fecha de realización vs fecha meta."""
    if isinstance(fecha_realizada, str):
        fecha_realizada = datetime.strptime(fecha_realizada, "%Y-%m-%d").date()
    if isinstance(fecha_meta, str):
        fecha_meta = datetime.strptime(fecha_meta, "%Y-%m-%d").date()
    
    if fecha_realizada <= fecha_meta:
        return "OPTIMO"
    else:
        diff = (fecha_realizada - fecha_meta).days
        if diff <= 3:
            return "MEDIO"
        else:
            return "BAJO"

def _upsert_registro_tarea(asignacion_id, usuario_id, fecha_realizada, rendimiento):
    """
    Inserta o actualiza un registro en registros_tareas.
    
    Evita duplicados usando asignacion_id + usuario_id como clave única.
    - Si existe: ACTUALIZA fecha_realizada y rendimiento
    - Si no existe: INSERTA nuevo registro
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verificar si ya existe un registro con esta combinación de asignacion_id + usuario_id
        cur.execute("""
            SELECT id FROM registros_tareas
            WHERE asignacion_id = %s AND usuario_id = %s
            LIMIT 1
        """, (asignacion_id, usuario_id))
        registro_existente = cur.fetchone()
        
        if registro_existente:
            # ACTUALIZAR: Si el registro ya existe, actualiza los valores
            cur.execute("""
                UPDATE registros_tareas
                SET fecha_realizada = %s, rendimiento = %s
                WHERE asignacion_id = %s AND usuario_id = %s
            """, (fecha_realizada, rendimiento, asignacion_id, usuario_id))
        else:
            # INSERTAR: Si no existe, crea un nuevo registro
            cur.execute("""
                INSERT INTO registros_tareas (asignacion_id, usuario_id, fecha_realizada, rendimiento)
                VALUES (%s, %s, %s, %s)
            """, (asignacion_id, usuario_id, fecha_realizada, rendimiento))
        
        conn.commit()
        return True
    except Exception as ex:
        conn.rollback()
        return False
    finally:
        cur.close(); conn.close()

def _update_progreso_tarea(asignacion_id, nuevo_estado, usuario_id, fecha_realizada, tarea_id, empresa_id, fecha_meta):
    """
    Actualiza el estado de la tarea y registra el progreso.
    
    Usa 'id' como referencia principal en asignaciones.
    
    Si nuevo_estado es "completada":
    - Obtiene TODAS las asignaciones del grupo (tarea_id, empresa_id, fecha_meta)
    - Registra en registros_tareas para cada usuario del grupo (evitando duplicados con UPSERT)
    - Actualiza TODAS las asignaciones del grupo a "completada"
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Calcular rendimiento basado en fecha_realizada y fecha_meta
        rendimiento = _calcular_rendimiento(fecha_realizada, fecha_meta)
        
        if nuevo_estado.lower() == "completada":
            # PASO 1: Obtener todas las asignaciones (id, usuario_id) del grupo
            grupo = _get_grupo_trabajo(tarea_id, empresa_id, fecha_meta)
            
            if not grupo:
                return False
            
            # PASO 2: Registrar progreso para cada usuario del grupo (evitando duplicados)
            for asig_dict in grupo:
                asig_id = asig_dict["id"]
                uid = asig_dict["usuario_id"]
                
                # Usar UPSERT para evitar duplicados
                _upsert_registro_tarea(asig_id, uid, fecha_realizada, rendimiento)
            
            # PASO 3: Actualizar todas las asignaciones del grupo a "completada"
            # Usar IN clause para actualizar todas en una sola query
            ids_grupo = [asig["id"] for asig in grupo]
            placeholders = ','.join(['%s'] * len(ids_grupo))
            cur.execute(f"""
                UPDATE asignaciones 
                SET estado = %s 
                WHERE id IN ({placeholders})
            """, ["completada"] + ids_grupo)
            
            conn.commit()
        else:
            # Para estados que no son completada, solo actualiza el actual
            _upsert_registro_tarea(asignacion_id, usuario_id, fecha_realizada, rendimiento)
            
            cur.execute("""
                UPDATE asignaciones 
                SET estado = %s 
                WHERE id = %s
            """, (nuevo_estado, asignacion_id))
            
            conn.commit()
        
        return True
    except Exception as ex:
        conn.rollback()
        return False
    finally:
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
            <div style='background: #f6c27d; color: #1e1e1e; padding: 12px 18px; border-radius: 12px; font-weight: 900; box-shadow: 0 4px 15px rgba(246, 194, 125, 0.2);'>
                ID #{detalle['id']}
            </div>
            <div>
                <h2 style='color: white; font-size: 24px; font-weight: 800; margin: 0;'>Detalles de la Actividad</h2>
                <p style='color: rgba(255,255,255,0.5); font-size: 13px; margin: 0;'>Revisión y actualización de progreso</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Formulario Elegante
    with st.container():
        st.markdown("<div style='background: rgba(255,255,255,0.02); padding: 30px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("📅 AÑO", value=str(detalle['anio']), disabled=True)
            st.text_input("🏢 EMPRESA", value=detalle['empresa'], disabled=True)
            st.markdown(f"**📋 TAREA**")
            st.markdown(f"<div style='background: rgba(246, 194, 125, 0.05); border: 1px solid rgba(246, 194, 125, 0.2); padding: 12px; border-radius: 8px; color: #f6c27d; font-weight: 600; margin-bottom: 15px;'>{detalle['tarea']}</div>", unsafe_allow_html=True)
            
        with col2:
            st.text_input("🗓️ MES", value=str(detalle['mes']).upper(), disabled=True)
            st.text_input("👤 ENCARGADO", value=detalle['encargado'], disabled=True)
            estado_opciones = ["pendiente", "en progreso", "completada"]
            nuevo_estado = st.selectbox("🔄 ACTUALIZAR ESTADO", estado_opciones, 
                                      index=estado_opciones.index(detalle['estado'].lower()) if detalle['estado'].lower() in estado_opciones else 0)

        c_meta, c_cant = st.columns(2)
        with c_meta:
            st.text_input("🎯 FECHA META", value=detalle['fecha_meta'].strftime("%d/%m/%Y"), disabled=True)
        with c_cant:
            fecha_realizada = st.date_input("✅ FECHA REALIZADA", value=datetime.now(), key="fecha_realizada_key")

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                success = _update_progreso_tarea(
                    detalle['id'], 
                    nuevo_estado,
                    detalle['usuario_id'],
                    fecha_realizada,
                    detalle['tarea_id'],
                    detalle['empresa_id'],
                    detalle['fecha_meta']
                )
                if success:
                    st.success("Progreso guardado.")
                else:
                    st.error("Error al guardar el progreso.")
        
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