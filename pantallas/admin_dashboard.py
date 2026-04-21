import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from styles.main import get_admin_style
from components.sidebar import admin_sidebar
from config.db import get_connection
from pantallas.admin_usuarios import admin_usuarios 
from pantallas.admin_empresas import admin_empresas
from pantallas.admin_asignacion_tareas import admin_asignacion_tarea


# ================================================================
#  FUNCIONES PARA OBTENER ESTADÍSTICAS
# ================================================================

def _get_stats_usuarios():
    """Obtiene estadísticas de usuarios"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN estado = 'activo' THEN 1 ELSE 0 END) as activos,
            SUM(CASE WHEN estado = 'inactivo' THEN 1 ELSE 0 END) as inactivos,
            rol
        FROM usuarios
        GROUP BY rol
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_stats_empresas():
    """Obtiene estadísticas de empresas"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN estado_contrato = 'Activo' THEN 1 ELSE 0 END) as activas,
            SUM(CASE WHEN estado_contrato != 'Activo' THEN 1 ELSE 0 END) as inactivas
        FROM empresas
    """)
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def _get_stats_tareas():
    """Obtiene estadísticas de tareas/asignaciones"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
            SUM(CASE WHEN estado = 'completada' THEN 1 ELSE 0 END) as completadas,
            SUM(CASE WHEN estado = 'vencida' THEN 1 ELSE 0 END) as vencidas
        FROM asignaciones
    """)
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def _get_usuarios_por_area():
    """Obtiene cantidad de usuarios por área"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre_area, COUNT(u.id) as cantidad
        FROM areas a
        LEFT JOIN subareas s ON a.id = s.area_id
        LEFT JOIN usuarios u ON s.id = u.subarea_id
        GROUP BY a.id, a.nombre_area
        ORDER BY cantidad DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_tareas_por_estado():
    """Obtiene tareas agrupadas por estado"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM asignaciones
        GROUP BY estado
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_tareas_ultimos_7_dias():
    """Obtiene tareas completadas en los últimos 7 días"""
    conn = get_connection()
    cur = conn.cursor()
    fecha_inicio = (datetime.now() - timedelta(days=7)).date()
    cur.execute("""
        SELECT DATE(fecha_creacion) as fecha, COUNT(*) as cantidad
        FROM asignaciones
        WHERE fecha_creacion >= %s
        GROUP BY DATE(fecha_creacion)
        ORDER BY fecha ASC
    """, (fecha_inicio,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_empresas_por_regimen():
    """Obtiene empresas agrupadas por régimen tributario"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT regimen_tributario, COUNT(*) as cantidad
        FROM empresas
        WHERE estado_contrato = 'Activo'
        GROUP BY regimen_tributario
        ORDER BY cantidad DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def admin_home():

    # ================= ESTILO GLOBAL =================
    st.markdown(get_admin_style(), unsafe_allow_html=True)

    # ================= USER =================
    user = st.session_state.get("user", {})

    # ================= SIDEBAR =================
    opcion = admin_sidebar(user)

    # ================= HEADER CONTENIDO =================
    st.markdown(f"""
    <div style="margin-bottom:25px;">
        <h1 class="page-title">Panel Admin</h1>
        <p class="page-subtitle">Bienvenido, {user.get('alias', 'Admin')}</p>
    </div>
""", unsafe_allow_html=True)

    st.divider()

    # ================= ROUTING =================
    if opcion == "Dashboard":
        
        # ============ ESTADÍSTICAS PRINCIPALES ============
        stats_usuarios = _get_stats_usuarios()
        stats_empresas = _get_stats_empresas()
        stats_tareas = _get_stats_tareas()
        
        total_usuarios = sum([row['total'] for row in stats_usuarios]) if stats_usuarios else 0
        total_usuarios_activos = sum([row['activos'] for row in stats_usuarios]) if stats_usuarios else 0
        total_empresas = stats_empresas['total'] if stats_empresas else 0
        total_empresas_activas = stats_empresas['activas'] if stats_empresas else 0
        total_tareas = stats_tareas['total'] if stats_tareas else 0
        tareas_pendientes = stats_tareas['pendientes'] if stats_tareas else 0

        # ============ TARJETAS MÉTRICAS ============
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">USUARIOS TOTALES</div>
                <div class="metric-value">{total_usuarios}</div>
                <div class="metric-subtitle">↳ {total_usuarios_activos} activos</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">EMPRESAS ACTIVAS</div>
                <div class="metric-value">{total_empresas_activas}/{total_empresas}</div>
                <div class="metric-subtitle">Contratos activos</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">TAREAS TOTALES</div>
                <div class="metric-value">{total_tareas}</div>
                <div class="metric-subtitle">↳ {tareas_pendientes} pendientes</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            tasa_completacion = round((stats_tareas['completadas'] / total_tareas * 100) if total_tareas > 0 else 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">TASA COMPLETACIÓN</div>
                <div class="metric-value">{tasa_completacion}%</div>
                <div class="metric-subtitle">{stats_tareas['completadas']} completadas</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ============ GRÁFICOS FILA 1 ============
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico: Estado de Tareas (Pie)
            tareas_por_estado = _get_tareas_por_estado()
            if tareas_por_estado:
                df_tareas = pd.DataFrame(tareas_por_estado)
                fig_tareas_estado = px.pie(
                    df_tareas,
                    values='cantidad',
                    names='estado',
                    title='Distribución de Tareas por Estado',
                    color_discrete_map={
                        'pendiente': '#f6c27d',
                        'completada': '#5DCAA5',
                        'vencida': '#F09595'
                    }
                )
                fig_tareas_estado.update_layout(height=350)
                st.plotly_chart(fig_tareas_estado, use_container_width=True)

        with col2:
            # Gráfico: Usuarios por Rol (Bar)
            if stats_usuarios:
                df_usuarios = pd.DataFrame(stats_usuarios)
                fig_usuarios_rol = px.bar(
                    df_usuarios,
                    x='rol',
                    y=['activos', 'inactivos'],
                    title='Usuarios por Rol y Estado',
                    labels={'value': 'Cantidad', 'rol': 'Rol'},
                    color_discrete_map={'activos': '#5DCAA5', 'inactivos': '#95949f'},
                    barmode='stack'
                )
                fig_usuarios_rol.update_layout(height=350)
                st.plotly_chart(fig_usuarios_rol, use_container_width=True)

        # ============ GRÁFICOS FILA 2 ============
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico: Usuarios por Área
            usuarios_por_area = _get_usuarios_por_area()
            if usuarios_por_area:
                df_areas = pd.DataFrame(usuarios_por_area)
                fig_areas = px.bar(
                df_areas.sort_values('cantidad', ascending=True),
                x='cantidad',
                y='nombre_area',
                title='Usuarios por Área',
                labels={'cantidad': 'Cantidad de Usuarios', 'nombre_area': 'Área'},
                color='cantidad',
                color_continuous_scale='Viridis',
                orientation='h'  # 🔥 clave
                )
                fig_areas.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_areas, use_container_width=True)

        with col2:
            # Gráfico: Empresas por Régimen Tributario
            empresas_regimen = _get_empresas_por_regimen()
            if empresas_regimen:
                df_regimen = pd.DataFrame(empresas_regimen)
                fig_regimen = px.bar(
                    df_regimen,
                    x='regimen_tributario',
                    y='cantidad',
                    title='Empresas Activas por Régimen Tributario',
                    labels={'cantidad': 'Cantidad', 'regimen_tributario': 'Régimen'},
                    color='cantidad',
                    color_continuous_scale='Blues'
                )
                fig_regimen.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_regimen, use_container_width=True)

        # ============ GRÁFICO FILA 3 ============
        # Gráfico: Tareas últimos 7 días
        tareas_7dias = _get_tareas_ultimos_7_dias()
        if tareas_7dias:
            df_7dias = pd.DataFrame(tareas_7dias)
            fig_7dias = px.line(
                df_7dias,
                x='fecha',
                y='cantidad',
                title='Tareas Creadas - Últimos 7 Días',
                markers=True,
                labels={'fecha': 'Fecha', 'cantidad': 'Cantidad de Tareas'}
            )
            fig_7dias.update_layout(height=350, hovermode='x unified')
            st.plotly_chart(fig_7dias, use_container_width=True)

    elif opcion == "Usuarios":
        admin_usuarios()  

    elif opcion == "Empresas":
        admin_empresas()
    elif opcion == "Asignaciones":
        admin_asignacion_tarea()