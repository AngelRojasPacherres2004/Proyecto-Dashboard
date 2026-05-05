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
#  PALETA DE COLORES CONSISTENTE
# ================================================================
COLORES = {
    "completada": "#5DCAA5",
    "pendiente":  "#F6C27D",
    "vencida":    "#F09595",
    "activo":     "#5DCAA5",
    "inactivo":   "#95949f",
    "primary":    "#4A90D9",
    "secondary":  "#7B68EE",
}

ESTADO_COLORS = {
    "completada": COLORES["completada"],
    "pendiente":  COLORES["pendiente"],
    "vencida":    COLORES["vencida"],
}

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    height=340,
)


# ================================================================
#  CONSULTAS A LA BASE DE DATOS
# ================================================================
def _get_stats_generales():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT rol,
               COUNT(*) AS total,
               SUM(CASE WHEN estado = 'activo'   THEN 1 ELSE 0 END) AS activos,
               SUM(CASE WHEN estado = 'inactivo' THEN 1 ELSE 0 END) AS inactivos
        FROM usuarios
        GROUP BY rol
    """)
    usuarios = cur.fetchall()

    cur.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN estado_contrato = 'Activo' THEN 1 ELSE 0 END) AS activas,
               SUM(CASE WHEN estado_contrato != 'Activo' THEN 1 ELSE 0 END) AS inactivas
        FROM empresas
    """)
    empresas = cur.fetchone()

    cur.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN estado = 'pendiente'  THEN 1 ELSE 0 END) AS pendientes,
               SUM(CASE WHEN estado = 'completada' THEN 1 ELSE 0 END) AS completadas,
               SUM(CASE WHEN estado = 'vencida'    THEN 1 ELSE 0 END) AS vencidas
        FROM asignaciones
    """)
    asignaciones = cur.fetchone()

    cur.close()
    conn.close()
    return usuarios, empresas, asignaciones

def _get_tareas_por_estado():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT estado, COUNT(*) AS cantidad
        FROM asignaciones
        GROUP BY estado
        ORDER BY cantidad DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_carga_por_usuario():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.nom_res AS nombre,
               COUNT(*) AS total,
               SUM(CASE WHEN a.estado = 'pendiente'  THEN 1 ELSE 0 END) AS pendientes,
               SUM(CASE WHEN a.estado = 'completada' THEN 1 ELSE 0 END) AS completadas,
               SUM(CASE WHEN a.estado = 'vencida'    THEN 1 ELSE 0 END) AS vencidas
        FROM asignaciones a
        JOIN usuarios u ON a.usuario_id = u.id
        GROUP BY u.id, u.nom_res
        ORDER BY total DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows
def _get_tareas_por_empresa():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.alias AS empresa,
               COUNT(*) AS total,
               SUM(CASE WHEN a.estado = 'completada' THEN 1 ELSE 0 END) AS completadas,
               SUM(CASE WHEN a.estado = 'pendiente'  THEN 1 ELSE 0 END) AS pendientes,
               SUM(CASE WHEN a.estado = 'vencida'    THEN 1 ELSE 0 END) AS vencidas
        FROM asignaciones a
        JOIN empresas e ON a.empresa_id = e.id
        GROUP BY e.id, e.alias
        ORDER BY total DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_completadas_por_mes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT TO_CHAR(fecha_meta, 'YYYY-MM') AS mes,
               COUNT(*) AS completadas
        FROM asignaciones
        WHERE estado = 'completada'
        GROUP BY mes
        ORDER BY mes ASC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_empresas_por_regimen():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(regimen_tributario, 'Sin régimen') AS regimen,
               COUNT(*) AS cantidad
        FROM empresas
        WHERE estado_contrato = 'Activo'
        GROUP BY regimen_tributario
        ORDER BY cantidad DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_tareas_por_proyecto():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.nombre_proyecto AS proyecto,
               a.estado,
               COUNT(*) AS cantidad
        FROM asignaciones a
        JOIN tareas t ON a.tarea_id = t.id
        JOIN proyectos p ON t.proyecto_id = p.id
        GROUP BY p.nombre_proyecto, a.estado
        ORDER BY proyecto, estado
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def _get_vencimiento_proximo():
    conn = get_connection()
    cur = conn.cursor()
    hoy = datetime.now().date()
    limite = hoy + timedelta(days=15)
    cur.execute("""
        SELECT u.alias AS usuario,
               e.alias AS empresa,
               t.nombre_tarea AS tarea,
               a.fecha_meta,
               (a.fecha_meta - CURRENT_DATE) AS dias_restantes
        FROM asignaciones a
        JOIN usuarios u ON a.usuario_id = u.id
        JOIN empresas e ON a.empresa_id = e.id
        JOIN tareas t   ON a.tarea_id   = t.id
        WHERE a.estado = 'pendiente'
          AND a.fecha_meta BETWEEN %s AND %s
        ORDER BY a.fecha_meta ASC
        LIMIT 20
    """, (hoy, limite))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

# ================================================================
#  FUNCIÓN PRINCIPAL
# ================================================================

def admin_home():

    st.markdown(get_admin_style(), unsafe_allow_html=True)

    user   = st.session_state.get("user", {})
    opcion = admin_sidebar(user)

    st.markdown(f"""
        <div style="margin-bottom:25px;">
            <h1 class="page-title">Panel Admin</h1>
            <p class="page-subtitle">Bienvenido, {user.get('alias', 'Admin')}</p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ================================================================
    #  ROUTING
    # ================================================================
    if opcion == "Dashboard":
        _render_dashboard()

    elif opcion == "Usuarios":
        admin_usuarios()

    elif opcion == "Empresas":
        admin_empresas()

    elif opcion == "Asignaciones":
        admin_asignacion_tarea()


# ================================================================
#  RENDER DEL DASHBOARD
# ================================================================

def _render_dashboard():

    # ── Carga de datos ──────────────────────────────────────────
    stats_usuarios, stats_empresas, stats_asig = _get_stats_generales()

    total_usuarios        = sum(r["total"]   for r in stats_usuarios) if stats_usuarios else 0
    total_activos         = sum(r["activos"] for r in stats_usuarios) if stats_usuarios else 0
    total_empresas        = stats_empresas["total"]   if stats_empresas else 0
    total_emp_activas     = stats_empresas["activas"] if stats_empresas else 0
    total_asignaciones    = stats_asig["total"]       if stats_asig else 0
    total_pendientes      = stats_asig["pendientes"]  if stats_asig else 0
    total_completadas     = stats_asig["completadas"] if stats_asig else 0
    total_vencidas        = stats_asig["vencidas"]    if stats_asig else 0
    tasa_completacion     = round(total_completadas / total_asignaciones * 100) if total_asignaciones else 0

    # ── KPI Cards ───────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)

    _kpi(col1, "USUARIOS",        total_usuarios,     f"↳ {total_activos} activos")
    _kpi(col2, "EMPRESAS ACTIVAS",f"{total_emp_activas}/{total_empresas}", "Contratos vigentes")
    _kpi(col3, "ASIGNACIONES",    total_asignaciones, f"↳ {total_pendientes} pendientes")
    _kpi(col4, "VENCIDAS",        total_vencidas,     "Requieren atención", color="#F09595")
    _kpi(col5, "TASA COMPLETACIÓN", f"{tasa_completacion}%", f"{total_completadas} completadas", color="#5DCAA5")

    st.divider()

    # ── Fila 1: Estado global + Carga por usuario ───────────────
    col1, col2 = st.columns([1, 2])

    with col1:
        data_estado = _get_tareas_por_estado()
        if data_estado:
            df = pd.DataFrame(data_estado)
            fig = px.pie(
                df, values="cantidad", names="estado",
                title="Estado de Asignaciones",
                color="estado",
                color_discrete_map=ESTADO_COLORS,
                hole=0.45,
            )
            fig.update_traces(textposition="outside", textinfo="percent+label")
            fig.update_layout(
                **LAYOUT_BASE,
                showlegend=False,
                title={
                    'y': 0.95,
                    'x': 0, 
                    'xanchor': 'left',
                    'yanchor': 'top'
                }
            )
            fig.update_layout(margin=dict(t=80, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        data_carga = _get_carga_por_usuario()
        if data_carga:
            df = pd.DataFrame(data_carga)
            df = df.sort_values("total", ascending=True)
            fig = go.Figure()
            for estado, color in [("completadas", COLORES["completada"]),
                                   ("pendientes",  COLORES["pendiente"]),
                                   ("vencidas",    COLORES["vencida"])]:
                fig.add_trace(go.Bar(
                    name=estado.capitalize(),
                    y=df["nombre"],
                    x=df[estado],
                    orientation="h",
                    marker_color=color,
                ))
            fig.update_layout(
                **LAYOUT_BASE,
                title="Carga de Trabajo por Usuario (Top 10)",
                barmode="stack",
                xaxis_title="Asignaciones",
                yaxis_title="",
                legend=dict(orientation="h", y=-0.35, x=0.5, xanchor='center'),
            )
            fig.update_layout(margin=dict(t=80, b=70, l=10, r=10)) # Aumentar margen superior e inferior
            st.plotly_chart(fig, use_container_width=True)

    # ── Fila 2: Tareas por empresa + Régimen tributario ─────────
    col1, col2 = st.columns(2)

    with col1:
        data_emp = _get_tareas_por_empresa()
        if data_emp:
            df = pd.DataFrame(data_emp).sort_values("total", ascending=True)
            fig = go.Figure()
            for estado, color in [("completadas", COLORES["completada"]),
                                   ("pendientes",  COLORES["pendiente"]),
                                   ("vencidas",    COLORES["vencida"])]:
                fig.add_trace(go.Bar(
                    name=estado.capitalize(),
                    y=df["empresa"],
                    x=df[estado],
                    orientation="h",
                    marker_color=color,
                ))
            fig.update_layout(
                **LAYOUT_BASE,
                title="Asignaciones por Empresa",
                barmode="stack",
                xaxis_title="Cantidad",
                yaxis_title="",
                legend=dict(orientation="h", y=-0.2),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        data_reg = _get_empresas_por_regimen()
        if data_reg:
            df = pd.DataFrame(data_reg)
            fig = px.bar(
                df, x="regimen", y="cantidad",
                title="Empresas Activas por Régimen Tributario",
                color="cantidad",
                color_continuous_scale="Blues",
                text="cantidad",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(**LAYOUT_BASE, xaxis_title="Régimen", yaxis_title="Empresas",
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    # ── Fila 3: Tendencia mensual + DJ vs PLAME ─────────────────
    col1, col2 = st.columns(2)

    with col1:
        data_mes = _get_completadas_por_mes()
        if data_mes:
            df = pd.DataFrame(data_mes)
            fig = px.area(
                df, x="mes", y="completadas",
                title="Tareas Completadas por Mes",
                labels={"mes": "Mes", "completadas": "Completadas"},
                color_discrete_sequence=[COLORES["completada"]],
            )
            fig.update_layout(**LAYOUT_BASE, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        data_proy = _get_tareas_por_proyecto()
        if data_proy:
            df = pd.DataFrame(data_proy)
            fig = px.bar(
                df, x="proyecto", y="cantidad", color="estado",
                title="Asignaciones por Proyecto",
                color_discrete_map=ESTADO_COLORS,
                barmode="group",
                text="cantidad",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(**LAYOUT_BASE, xaxis_title="Proyecto", yaxis_title="Asignaciones",
                              legend_title="Estado")
            st.plotly_chart(fig, use_container_width=True)

    # ── Fila 4: Tabla de próximos vencimientos ──────────────────
    st.subheader("⚠️ Asignaciones por Vencer (próximos 15 días)")
    data_venc = _get_vencimiento_proximo()
    if data_venc:
        df = pd.DataFrame(data_venc)
        df["fecha_meta"] = pd.to_datetime(df["fecha_meta"]).dt.strftime("%d/%m/%Y")
        df.columns = ["Usuario", "Empresa", "Tarea", "Fecha Meta", "Días Restantes"]

        def _color_dias(val):
            if val <= 3:
                return "background-color:#F09595; color:#7a0000; font-weight:bold"
            elif val <= 7:
                return "background-color:#F6C27D; color:#7a4000"
            return ""

        styled = df.style.map(_color_dias, subset=["Días Restantes"])
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No hay asignaciones pendientes por vencer en los próximos 15 días.")


# ================================================================
#  HELPER: tarjeta KPI
# ================================================================

def _kpi(col, label: str, value, subtitle: str = "", color: str = "#4A90D9"):
    with col:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid {color};">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};">{value}</div>
            <div class="metric-subtitle">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)