import streamlit as st
import pandas as pd
from datetime import datetime, date
from components.ui import page_header, section_header, metric_card
from components.sidebar import trabajador_sidebar
from styles.main import get_admin_style
from config.db import get_connection

# ================================================================
#  HELPERS - COMPATIBILIDAD DE CURSOR
# ================================================================

def get_val(item, key, index):
    """Mapeo seguro (soporta dict o tuple según la configuración del cursor)."""
    if item is None: return None
    if isinstance(item, dict): return item.get(key)
    return item[index]

# ================================================================
#  REPOSITORIO - CONSULTAS REALES
# ================================================================

def _get_metricas_usuario(user_id: int):
    """Calcula métricas reales basadas en la tabla asignaciones."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Tareas para hoy
    cur.execute("""
        SELECT COUNT(*) as total FROM asignaciones 
        WHERE usuario_id = %s AND fecha_meta = CURRENT_DATE
    """, (user_id,))
    res_hoy = cur.fetchone()
    hoy = get_val(res_hoy, 'total', 0)
    
    # Tareas de la semana
    cur.execute("""
        SELECT COUNT(*) as total FROM asignaciones 
        WHERE usuario_id = %s AND YEARWEEK(fecha_meta, 1) = YEARWEEK(CURDATE(), 1)
    """, (user_id,))
    res_sem = cur.fetchone()
    semana = get_val(res_sem, 'total', 0)
    
    # Eficiencia (Completadas / Totales)
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN estado = 'completada' THEN 1 END) as comp,
            COUNT(*) as total
        FROM asignaciones WHERE usuario_id = %s
    """, (user_id,))
    res = cur.fetchone()
    comp = get_val(res, 'comp', 0)
    total = get_val(res, 'total', 0)
    eficiencia = f"{(comp/total*100):.0f}%" if total > 0 else "0%"
    
    cur.close(); conn.close()
    return str(hoy or 0), str(semana or 0), eficiencia

def _get_tareas_pendientes_db(user_id: int):
    """Obtiene las asignaciones pendientes de la base de datos."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            t.nombre_tarea as titulo,
            e.razon_social as empresa,
            a.fecha_meta,
            a.estado,
            a.peso
        FROM asignaciones a
        JOIN tareas t ON a.tarea_id = t.id
        JOIN empresas e ON a.empresa_id = e.id
        WHERE a.usuario_id = %s AND a.estado != 'completada'
        ORDER BY a.fecha_meta ASC
    """, (user_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_actividad_reciente_db(user_id: int):
    """Obtiene los últimos registros de tareas realizadas."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            t.nombre_tarea, 
            rt.fecha_realizada,
            e.razon_social
        FROM registros_tareas rt
        JOIN asignaciones a ON rt.asignacion_id = a.id
        JOIN tareas t ON a.tarea_id = t.id
        JOIN empresas e ON a.empresa_id = e.id
        WHERE a.usuario_id = %s
        ORDER BY rt.id DESC LIMIT 3
    """, (user_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_empresas_activas():
    """Obtiene las empresas activas de la base de datos."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, razon_social
        FROM empresas
        WHERE estado_contrato = 'Activo'
        ORDER BY razon_social
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_proyectos():
    """Obtiene los proyectos de la base de datos."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_proyecto FROM proyectos ORDER BY nombre_proyecto")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_tareas_all():
    """Obtiene todas las tareas de la base de datos."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_tarea, proyecto_id FROM tareas ORDER BY nombre_tarea")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _registrar_tarea_db(data: dict):
    """Inserta la tarea en asignaciones y crea el registro de cumplimiento."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Crear la asignación como completada
        cur.execute("""
            INSERT INTO asignaciones (usuario_id, empresa_id, tarea_id, fecha_meta, estado, peso)
            VALUES (%s, %s, %s, %s, 'completada', %s)
        """, (data['usuario_id'], data['empresa_id'], data['tarea_id'], 
              data['fecha_meta'], data['peso']))
        
        asig_id = cur.lastrowid

        # 2. Crear el registro de la tarea realizada
        cur.execute("""
            INSERT INTO registros_tareas (asignacion_id, fecha_realizada, rendimiento)
            VALUES (%s, %s, %s)
        """, (asig_id, data['fecha_realizada'], data['rendimiento']))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error al guardar: {e}")
        return False
    finally:
        cur.close(); conn.close()

def _form_registro_tarea(user_alias: str, user_id: int):
    """Formulario para el registro de nuevas tareas por el trabajador."""
    empresas = _get_empresas_activas()
    proyectos = _get_proyectos()
    tareas_all = _get_tareas_all()

    emp_map = {get_val(e, 'razon_social', 1): get_val(e, 'id', 0) for e in empresas}
    proj_map = {get_val(p, 'nombre_proyecto', 1): get_val(p, 'id', 0) for p in proyectos}

    emp_names = list(emp_map.keys())
    proj_names = list(proj_map.keys())

    with st.container(border=True):
        st.markdown('<h3 style="color:#f6c27d; text-align:center;">FORMULARIO DE REGISTRO</h3>', unsafe_allow_html=True)
        
        with st.form("form_registro_trabajador"):
            col1, col2 = st.columns(2)
            with col1:
                ano = st.number_input("AÑO", min_value=2020, max_value=date.today().year + 2, value=date.today().year)
                empresa_sel = st.selectbox("EMPRESA", ["Seleccionar"] + emp_names)
                proyecto_sel = st.selectbox("PROYECTO", ["Seleccionar"] + proj_names)
                
                # Filtrar tareas dinámicamente según el proyecto seleccionado
                tareas_filtradas = []
                if proyecto_sel != "Seleccionar":
                    p_id = proj_map[proyecto_sel]
                    tareas_filtradas = [t for t in tareas_all if get_val(t, 'proyecto_id', 2) == p_id]
                else:
                    tareas_filtradas = tareas_all
                
                tar_names = [get_val(t, 'nombre_tarea', 1) for t in tareas_filtradas]
                tarea_sel = st.selectbox("TAREA", ["Seleccionar"] + tar_names)
                mes_t = st.number_input("MES T", min_value=1, max_value=12, value=date.today().month)

            with col2:
                st.text_input("ENCARGADO", value=user_alias, disabled=True)
                f_realizada = st.date_input("FECHA REALIZADA", value=date.today())
                f_meta = st.date_input("FECHA META", value=date.today())
                cant = st.number_input("CANT", min_value=0, value=1)
                prioridad = st.selectbox("PRIORIDAD", ["Baja", "Media", "Alta"])

            if st.form_submit_button("Registrar Tarea", use_container_width=True):
                if "Seleccionar" in [empresa_sel, proyecto_sel, tarea_sel]:
                    st.error("Por favor, complete todos los campos de selección.")
                else:
                    # Mapeo de IDs
                    e_id = emp_map[empresa_sel]
                    # Buscar el ID de la tarea seleccionada en la lista original
                    t_id = next(get_val(t, 'id', 0) for t in tareas_all if get_val(t, 'nombre_tarea', 1) == tarea_sel)
                    
                    # Mapeo de prioridad a pesos y rendimiento de la BD
                    mapping = {
                        "Baja":  (1, 'MEDIO'),
                        "Media": (2, 'OPTIMO'),
                        "Alta":  (3, 'URGENTE')
                    }
                    peso, rend = mapping[prioridad]

                    exito = _registrar_tarea_db({
                        "usuario_id": user_id,
                        "empresa_id": e_id,
                        "tarea_id": t_id,
                        "fecha_meta": f_meta,
                        "fecha_realizada": f_realizada,
                        "peso": peso,
                        "rendimiento": rend
                    })
                    if exito:
                        st.success(f"Tarea '{tarea_sel}' registrada correctamente.")
                        st.balloons()

def trabajador_home():
    # ================= ESTILO =================
    st.markdown(get_admin_style(), unsafe_allow_html=True)

    user = st.session_state.get("user", {})
    user_id = user.get("id")
    user_alias = user.get("alias", "Trabajador")

    if not user_id:
        st.error("Sesión no válida")
        return

    # ================= SIDEBAR (NAVEGACIÓN) =================
    opcion = trabajador_sidebar(user)

    # ================= CONTENIDO DINÁMICO =================
    if opcion == "Registro":
        page_header("Registro de Tareas", "Ingresa el detalle de la actividad realizada")
        _form_registro_tarea(user_alias, user_id)
        return

    # Si la opción es "Reportes" (Dashboard)
    page_header("Panel de Trabajador", f"Bienvenido, {user.get('alias', 'Trabajador')}")

    # Obtener datos de la base de datos
    t_hoy, t_semana, t_efi = _get_metricas_usuario(user_id)
    tareas_db = _get_tareas_pendientes_db(user_id)
    actividad_db = _get_actividad_reciente_db(user_id)

    # ================= MÉTRICAS PERSONALES =================
    section_header("Mi Rendimiento", "Tus estadísticas del mes actual", "📊")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Tareas Hoy", t_hoy, "✅")

    with col2:
        metric_card("Tareas Semana", t_semana, "📅")

    with col3:
        metric_card("Eficiencia", t_efi, "🎯")

    with col4:
        metric_card("Puntuación", "4.7", "⭐")

    st.markdown("---")

    # ================= TAREAS PENDIENTES =================
    section_header("Tareas Pendientes", "Actividades que requieren tu atención", "📋")

    if not tareas_db:
        st.info("No tienes tareas pendientes asignadas.")
    
    for tarea in tareas_db:
        # Lógica de prioridad basada en el peso (definido en tu tabla asignaciones)
        t_peso = get_val(tarea, 'peso', 4)
        prioridad = "Alta" if t_peso >= 3 else "Media" if t_peso == 2 else "Baja"
        prioridad_color = {"Alta": "#ff6b6b", "Media": "#ffd93d", "Baja": "#6bcf7f"}.get(prioridad, "#6bcf7f")
        
        fecha_fmt = get_val(tarea, 'fecha_meta', 2).strftime("%d/%m/%Y")
        estado_icono = {"pendiente": "⏳", "vencida": "⚠️"}.get(get_val(tarea, 'estado', 3), "⏳")

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
                        <h4 style="color: white; margin: 0; font-size: 16px; font-weight: 600;">{get_val(tarea, 'titulo', 0)} 
                        <span style="color:rgba(255,255,255,0.4); font-weight:400; font-size:13px;">- {get_val(tarea, 'empresa', 1)}</span></h4>
                    </div>
                    <div style="display: flex; gap: 16px; font-size: 14px;">
                        <span style="color: {prioridad_color};">🔥 {prioridad}</span>
                        <span style="color: rgba(255,255,255,0.7);">📅 Meta: {fecha_fmt}</span>
                        <span style="color: rgba(255,255,255,0.7); text-transform: capitalize;">{get_val(tarea, 'estado', 3)}</span>
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

    if not actividad_db:
        st.caption("No hay actividad reciente registrada.")

    for act in actividad_db:
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
            <span style="font-size: 16px; margin-right: 12px;">✅</span>
            <div style="flex: 1; color: rgba(255,255,255,0.9);">
                Completaste: <b>{act[0]}</b> para {act[2]}
            </div>
            <span style="color: rgba(255,255,255,0.5); font-size: 12px;">{act[1].strftime("%d/%m/%Y")}</span>
        </div>
        """, unsafe_allow_html=True) 