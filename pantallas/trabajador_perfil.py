import streamlit as st
from config.db import get_connection
from styles.main import get_admin_style
from components.ui import section_header, metric_card
from datetime import datetime

def _get_user_full_data(uid):
    """Obtiene datos detallados del usuario incluyendo área y subárea."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT u.nom_res, u.alias, u.usuario, u.rol, u.estado, u.fecha_creacion,
                   a.nombre_area, s.nombre_subarea
            FROM usuarios u
            LEFT JOIN subareas s ON u.subarea_id = s.id
            LEFT JOIN areas a ON s.area_id = a.id
            WHERE u.id = %s
        """, (uid,))
        row = cur.fetchone()
        
        if row:
            # Acceso seguro: detecta si 'row' es un diccionario o una tupla/lista
            if isinstance(row, dict):
                return {
                    'nom_res': row.get('nom_res'),
                    'alias': row.get('alias'),
                    'usuario': row.get('usuario'),
                    'rol': row.get('rol'),
                    'estado': row.get('estado'),
                    'fecha_creacion': row.get('fecha_creacion'),
                    'nombre_area': row.get('nombre_area'),
                    'nombre_subarea': row.get('nombre_subarea')
                }
            else:
                # Es una tupla o lista
                return {
                    'nom_res': row[0],
                    'alias': row[1],
                    'usuario': row[2],
                    'rol': row[3],
                    'estado': row[4],
                    'fecha_creacion': row[5],
                    'nombre_area': row[6],
                    'nombre_subarea': row[7]
                }
        return None
    finally:
        cur.close()
        conn.close()

def _get_user_performance_stats(uid):
    """Calcula estadísticas reales de rendimiento para el mes actual."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # 1. Tareas asignadas para hoy
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM asignaciones 
            WHERE usuario_id = %s AND fecha_meta::date = CURRENT_DATE
        """, (uid,))
        row_hoy = cur.fetchone()
        # Acceso seguro para el conteo
        hoy = row_hoy['total'] if isinstance(row_hoy, dict) else (row_hoy[0] if row_hoy else 0)
        
        # 2. Tareas asignadas en la semana actual
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM asignaciones 
            WHERE usuario_id = %s 
AND DATE_TRUNC('week', fecha_meta) = DATE_TRUNC('week', CURRENT_DATE)
        """, (uid,))
        row_sem = cur.fetchone()
        semana = row_sem['total'] if isinstance(row_sem, dict) else (row_sem[0] if row_sem else 0)
        
        # 3. Estadísticas mensuales para Eficiencia y Puntuación
        cur.execute("""
            SELECT 
                COUNT(*) as total, 
                SUM(CASE WHEN rendimiento IN ('OPTIMO', 'URGENTE') THEN 1 ELSE 0 END) as optimas,
                AVG(CASE 
                    WHEN rendimiento = 'URGENTE' THEN 5.0
                    WHEN rendimiento = 'OPTIMO' THEN 4.5
                    WHEN rendimiento = 'MEDIO' THEN 3.0
                    WHEN rendimiento = 'BAJO' THEN 1.0
                    ELSE 0.0
                END) as promedio
            FROM registros_tareas 
            WHERE usuario_id = %s 
            AND EXTRACT(MONTH FROM fecha_realizada) = EXTRACT(MONTH FROM CURRENT_DATE)
AND EXTRACT(YEAR FROM fecha_realizada) = EXTRACT(YEAR FROM CURRENT_DATE)
        """, (uid,))
        res_mes = cur.fetchone()

        if isinstance(res_mes, dict):
            total_mes = res_mes.get('total') or 0
            optimas_mes = res_mes.get('optimas') or 0
            puntuacion_avg = res_mes.get('promedio') or 0
        else:
            total_mes = res_mes[0] if res_mes and res_mes[0] is not None else 0
            optimas_mes = res_mes[1] if res_mes and res_mes[1] is not None else 0
            puntuacion_avg = res_mes[2] if res_mes and res_mes[2] is not None else 0

        eficiencia = (optimas_mes / total_mes * 100) if total_mes > 0 else 0

        return {
            "hoy": hoy,
            "semana": semana,
            "eficiencia": round(eficiencia),
            "puntuacion": round(float(puntuacion_avg), 1)
        }
    except Exception as e:
        st.error(f"Error al calcular estadísticas: {e}")
        return {"hoy": 0, "semana": 0, "eficiencia": 0, "puntuacion": 0}
    finally:
        cur.close()
        conn.close()

def trabajador_perfil():
    user_session = st.session_state.get("user", {})
    user_id = user_session.get("id")
    
    if not user_id:
        st.error("No se encontró información de sesión activa.")
        return

    user_data = _get_user_full_data(user_id)
    if not user_data:
        st.error("No se pudieron cargar los datos del usuario.")
        return
    
    st.markdown("""
        <div style='margin-bottom: 2rem;'>
            <h2 style='color: #f6c27d; font-size: 24px; font-weight: 800; margin: 0;'>Configuración de Perfil</h2>
            <p style='color: rgba(255,255,255,0.5); font-size: 13px;'>Administra tu información personal y credenciales de acceso</p>
        </div>
    """, unsafe_allow_html=True)

    # --- HEADER DE PERFIL ---
    alias = user_data.get('alias', 'U')
    nombre = user_data.get('nom_res', 'Usuario')
    rol = user_data.get('rol', 'N/A')
    estado = user_data.get('estado', 'N/A')

    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(246, 194, 125, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
            padding: 35px;
            border-radius: 20px;
            border: 1px solid rgba(246, 194, 125, 0.15);
            display: flex;
            align-items: center;
            margin-bottom: 30px;
        ">
            <div style="
                width: 90px;
                height: 90px;
                background: #f6c27d;
                color: #1e1e1e;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 36px;
                font-weight: 900;
                margin-right: 25px;
                box-shadow: 0 10px 25px rgba(246, 194, 125, 0.2);
            ">
                {alias[0].upper() if alias else 'U'}
            </div>
            <div>
                <h2 style="margin: 0; color: white; font-size: 24px; font-weight: 700;">{nombre}</h2>
                <div style="display: flex; gap: 10px; margin-top: 8px;">
                    <span style="background: rgba(133, 183, 235, 0.12); color: #85B7EB; padding: 2px 12px; border-radius: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase;">
                        {rol}
                    </span>
                    <span style="background: rgba(93, 202, 165, 0.12); color: #5DCAA5; padding: 2px 12px; border-radius: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase;">
                        {estado}
                    </span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h4 style='color: white; margin-bottom: 1rem; font-size: 16px;'>Información de Cuenta</h4>", unsafe_allow_html=True)
    
    fecha_creacion = user_data.get('fecha_creacion')
    fecha_str = fecha_creacion.strftime("%d/%m/%Y") if isinstance(fecha_creacion, datetime) else str(fecha_creacion) if fecha_creacion else "—"
    
    info_items = [
        ("Alias Institucional", user_data.get('alias', '—')),
        ("Nombre de Usuario", f"@{user_data.get('usuario', '—')}"),
        ("Área / Departamento", user_data.get('nombre_area') or "General"),
        ("Subárea Asignada", user_data.get('nombre_subarea') or "—"),
        ("Fecha de Ingreso", fecha_str)
    ]

    st.markdown("""
        <div style="display:flex; flex-direction:column; gap:14px; max-width: 580px;">
    """, unsafe_allow_html=True)

    for label, val in info_items:
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.06); padding: 18px 20px; border-radius: 18px; margin-bottom: 0; border: 1px solid rgba(246,194,125,0.14);">
                <div style="color: rgba(255,255,255,0.45); font-size: 11px; text-transform: uppercase; letter-spacing: 1.4px; font-weight: 700; margin-bottom: 8px;">{label}</div>
                <div style="color: white; font-size: 16px; font-weight: 700; line-height: 1.4;">{val}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        </div>
    """, unsafe_allow_html=True)

    # --- SECCIÓN DE RENDIMIENTO ---
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    section_header("Mi Rendimiento", "Tus estadísticas del mes actual", "-")
    
    stats = _get_user_performance_stats(user_id)
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        metric_card("Tareas Hoy", str(stats['hoy']), "✔")

    with col_m2:
        metric_card("Tareas Semana", str(stats['semana']), "🗓")

    with col_m3:
        metric_card("Eficiencia", f"{stats['eficiencia']}%", "🎯")

    with col_m4:
        metric_card("Puntuación", str(stats['puntuacion']), "☆")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
