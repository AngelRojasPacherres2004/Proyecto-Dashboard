import streamlit as st
from config.db import get_connection
from styles.main import get_admin_style
from components.ui import section_header, metric_card

def _get_user_full_data(uid):
    """Obtiene datos detallados del usuario incluyendo área y subárea."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.nom_res, u.alias, u.usuario, u.rol, u.estado, u.fecha_creacion,
               a.nombre_area, s.nombre_subarea
        FROM usuarios u
        LEFT JOIN subareas s ON u.subarea_id = s.id
        LEFT JOIN areas a ON s.area_id = a.id
        WHERE u.id = %s
    """, (uid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def _update_password(uid, new_password):
    """Actualiza la contraseña del usuario."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET password = %s WHERE id = %s", (new_password, uid))
    conn.commit()
    cur.close(); conn.close()

def trabajador_perfil():
    user_session = st.session_state.get("user", {})
    user_id = user_session.get("id")
    
    if not user_id:
        st.error("No se encontró información de sesión activa.")
        return

    user_data = _get_user_full_data(user_id)
    
    st.markdown("""
        <div style='margin-bottom: 2rem;'>
            <h2 style='color: #f6c27d; font-size: 24px; font-weight: 800; margin: 0;'>Configuración de Perfil</h2>
            <p style='color: rgba(255,255,255,0.5); font-size: 13px;'>Administra tu información personal y credenciales de acceso</p>
        </div>
    """, unsafe_allow_html=True)

    # --- HEADER DE PERFIL (AVATAR ELEGANTE) ---
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
                {user_data['alias'][0].upper() if user_data['alias'] else 'U'}
            </div>
            <div>
                <h2 style="margin: 0; color: white; font-size: 24px; font-weight: 700;">{user_data['nom_res']}</h2>
                <div style="display: flex; gap: 10px; margin-top: 8px;">
                    <span style="background: rgba(133, 183, 235, 0.12); color: #85B7EB; padding: 2px 12px; border-radius: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase;">
                        {user_data['rol']}
                    </span>
                    <span style="background: rgba(93, 202, 165, 0.12); color: #5DCAA5; padding: 2px 12px; border-radius: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase;">
                        {user_data['estado']}
                    </span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 0.9], gap="large")
    with col1:
        st.markdown("<h4 style='color: white; margin-bottom: 1.2rem; font-size: 16px;'>Información de Cuenta</h4>", unsafe_allow_html=True)
        
        info_cols = st.columns(2)
        info_items = [
            ("Alias Institucional", user_data['alias']),
            ("Nombre de Usuario", f"@{user_data['usuario']}"),
            ("Área / Departamento", user_data['nombre_area'] or "General"),
            ("Subárea Asignada", user_data['nombre_subarea'] or "—"),
            ("Fecha de Ingreso", user_data['fecha_creacion'].strftime("%d/%m/%Y") if user_data['fecha_creacion'] else "—")
        ]

        for i, (label, val) in enumerate(info_items):
            with info_cols[i % 2]:
                st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 12px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.06);">
                        <div style="color: rgba(255,255,255,0.4); font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; margin-bottom: 4px;">{label}</div>
                        <div style="color: white; font-size: 14px; font-weight: 600;">{val}</div>
                    </div>
                """, unsafe_allow_html=True)


  # --- SECCIÓN DE RENDIMIENTO ---
    section_header("Mi Rendimiento", "Tus estadísticas del mes actual", "📊")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        metric_card("Tareas Hoy", "8", "✔")

    with col_m2:
        metric_card("Tareas Semana", "42", "🗓")

    with col_m3:
        metric_card("Eficiencia", "91%", "🎯")

    with col_m4:
        metric_card("Puntuación", "4.7", "☆")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

   
