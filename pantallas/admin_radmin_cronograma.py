import streamlit as st
import pandas as pd
import calendar
from datetime import date
from config.db import get_connection


# ─────────────────────────────────────────────────────────────
#  DB helpers
# ─────────────────────────────────────────────────────────────

def _ensure_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS radmin_cronograma (
            id BIGSERIAL PRIMARY KEY,
            tarea_planeada TEXT NOT NULL,
            fecha_objetivo DATE NOT NULL,
            prioridad SMALLINT NOT NULL DEFAULT 1,
            notas TEXT NULL,
            archivo_nombre TEXT NULL,
            archivo_data BYTEA NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente_plan',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def _insert_item(tarea, fecha_objetivo, prioridad, notas=None,
                 archivo_nombre=None, archivo_data=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO radmin_cronograma
        (tarea_planeada, fecha_objetivo, prioridad, notas, archivo_nombre, archivo_data, estado)
        VALUES (%s, %s, %s, %s, %s, %s, 'pendiente_plan')
        """,
        (tarea, fecha_objetivo, prioridad, notas, archivo_nombre, archivo_data),
    )
    conn.commit()
    cur.close()
    conn.close()


def _list_items():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, tarea_planeada, fecha_objetivo, prioridad, notas,
               archivo_nombre, estado, created_at
        FROM radmin_cronograma
        ORDER BY fecha_objetivo ASC, id DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def _delete_item(item_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM radmin_cronograma WHERE id = %s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()


# ─────────────────────────────────────────────────────────────
#  Color helpers
# ─────────────────────────────────────────────────────────────

# Each priority band has light + dark variants
PRIORIDAD_STYLES = {
    "baja":  {
        "light": {"bg": "#e8f5e9", "border": "#43a047", "text": "#1b5e20"},
        "dark":  {"bg": "#1b3320", "border": "#43a047", "text": "#81c784"},
    },
    "media": {
        "light": {"bg": "#fff8e1", "border": "#fb8c00", "text": "#e65100"},
        "dark":  {"bg": "#2e2100", "border": "#fb8c00", "text": "#ffb74d"},
    },
    "alta":  {
        "light": {"bg": "#fce4ec", "border": "#e53935", "text": "#b71c1c"},
        "dark":  {"bg": "#2d1217", "border": "#e53935", "text": "#ef9a9a"},
    },
}

ESTADO_STYLES = {
    "pendiente_plan": {
        "light": {"bg": "#ede7f6", "text": "#4527a0"},
        "dark":  {"bg": "#1e1530", "text": "#ce93d8"},
        "label": "Pendiente",
    },
    "en_progreso": {
        "light": {"bg": "#e3f2fd", "text": "#0d47a1"},
        "dark":  {"bg": "#0d1e35", "text": "#90caf9"},
        "label": "En progreso",
    },
    "completado": {
        "light": {"bg": "#e8f5e9", "text": "#1b5e20"},
        "dark":  {"bg": "#0d2318", "text": "#a5d6a7"},
        "label": "Completado",
    },
    "cancelado": {
        "light": {"bg": "#fce4ec", "text": "#b71c1c"},
        "dark":  {"bg": "#2d1217", "text": "#ef9a9a"},
        "label": "Cancelado",
    },
}


def _prio_band(prioridad: int) -> str:
    if prioridad <= 3:
        return "baja"
    if prioridad <= 6:
        return "media"
    return "alta"


def _get_prioridad_style(prioridad: int, dark: bool) -> dict:
    band = _prio_band(prioridad)
    mode = "dark" if dark else "light"
    s = PRIORIDAD_STYLES[band][mode].copy()
    s["label"] = band.capitalize()
    return s


def _get_estado_style(estado: str, dark: bool) -> dict:
    info = ESTADO_STYLES.get(estado, {
        "light": {"bg": "#f5f5f5", "text": "#333"},
        "dark":  {"bg": "#2a2a2a", "text": "#ccc"},
        "label": estado,
    })
    mode = "dark" if dark else "light"
    return {"label": info["label"], **info[mode]}


# ─────────────────────────────────────────────────────────────
#  Calendar HTML builder
# ─────────────────────────────────────────────────────────────

MONTH_NAMES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
DAYS_HEADER = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _render_calendar_html(rows, year: int, month: int, dark: bool) -> str:
    tasks_by_date: dict[date, list] = {}
    for r in rows:
        fd = r["fecha_objetivo"]
        if not isinstance(fd, date):
            fd = fd.date()
        tasks_by_date.setdefault(fd, []).append(r)

    cal = calendar.monthcalendar(year, month)
    today = date.today()

    day_cells_html = ""
    for week in cal:
        for day_num in week:
            if day_num == 0:
                day_cells_html += '<div class="cal-cell cal-empty"></div>'
                continue

            current_date = date(year, month, day_num)
            is_today   = current_date == today
            is_weekend = current_date.weekday() >= 5
            day_tasks  = tasks_by_date.get(current_date, [])

            cell_class = "cal-cell"
            if is_today:
                cell_class += " cal-today"
            elif is_weekend:
                cell_class += " cal-weekend"

            tasks_html = ""
            for t in day_tasks[:3]:
                ps = _get_prioridad_style(t["prioridad"], dark)
                name = t["tarea_planeada"]
                name = name[:26] + "…" if len(name) > 26 else name
                tasks_html += (
                    f'<div class="cal-task" style="'
                    f'background:{ps["bg"]};'
                    f'border-left:3px solid {ps["border"]};'
                    f'color:{ps["text"]};">{name}</div>'
                )
            if len(day_tasks) > 3:
                tasks_html += f'<div class="cal-more">+{len(day_tasks)-3} más</div>'

            num_class = "cal-day-num"
            if is_today:
                num_class += " cal-day-today-num"

            day_cells_html += (
                f'<div class="{cell_class}">'
                f'<div class="{num_class}">{day_num}</div>'
                f'<div class="cal-tasks-wrap">{tasks_html}</div>'
                f'</div>'
            )

    # ── CSS variables per mode ──────────────────────────────────
    if dark:
        v = {
            "bg_page":     "transparent",
            "bg_grid":     "#13131f",
            "bg_cell":     "#1a1a2e",
            "bg_empty":    "#111120",
            "bg_weekend":  "#1e1830",
            "bg_today":    "#0e1540",
            "border_cell": "#252540",
            "text_month":  "#e8e8ff",
            "text_day":    "#9090b8",
            "text_more":   "#6060a0",
            "header_bg":   "#0d0d1a",
            "header_text": "rgba(246,194,125,0.9)",
            "header_wknd": "rgba(246,194,125,0.4)",
            "badge_bg":    "#0d0d1a",
            "badge_text":  "#f6c27d",
            "legend_text": "#8888b0",
            "today_accent":"#5c7cfa",
            "today_num_bg":"#3d5afe",
        }
    else:
        v = {
            "bg_page":     "transparent",
            "bg_grid":     "#ffffff",
            "bg_cell":     "#ffffff",
            "bg_empty":    "#f8f8fc",
            "bg_weekend":  "#fdf8ff",
            "bg_today":    "#f0f4ff",
            "border_cell": "#ebebf5",
            "text_month":  "#1a1a2e",
            "text_day":    "#5a5a7a",
            "text_more":   "#9090b0",
            "header_bg":   "#1a1a2e",
            "header_text": "rgba(246,194,125,0.85)",
            "header_wknd": "rgba(246,194,125,0.4)",
            "badge_bg":    "#1a1a2e",
            "badge_text":  "#f6c27d",
            "legend_text": "#666680",
            "today_accent":"#3d5afe",
            "today_num_bg":"#3d5afe",
        }

    css = f"""
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

.cronograma-root {{
    font-family: 'DM Sans', sans-serif;
    padding: 0; margin: 0;
    background: {v['bg_page']};
}}
.cal-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    padding: 0 4px;
}}
.cal-month-title {{
    font-size: 28px;
    font-weight: 600;
    color: {v['text_month']};
    letter-spacing: -0.5px;
}}
.cal-year-badge {{
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    background: {v['badge_bg']};
    color: {v['badge_text']};
    padding: 4px 14px;
    border-radius: 20px;
    letter-spacing: 1px;
}}
.cal-legend {{
    display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
}}
.cal-legend-item {{
    display: flex; align-items: center; gap: 6px;
    font-size: 12px; color: {v['legend_text']};
}}
.cal-legend-dot {{
    width: 10px; height: 10px; border-radius: 3px;
}}
.cal-grid-wrap {{
    background: {v['bg_grid']};
    border-radius: 20px;
    border: 1px solid {v['border_cell']};
    overflow: hidden;
    box-shadow: 0 4px 32px rgba(0,0,0,{'0.35' if dark else '0.07'});
}}
.cal-days-header {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    background: {v['header_bg']};
}}
.cal-days-header div {{
    text-align: center;
    padding: 14px 0;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.9px;
    text-transform: uppercase;
    color: {v['header_text']};
}}
.cal-days-header div:nth-child(6),
.cal-days-header div:nth-child(7) {{
    color: {v['header_wknd']};
}}
.cal-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
}}
.cal-cell {{
    min-height: 110px;
    padding: 10px 10px 8px;
    border-right: 1px solid {v['border_cell']};
    border-bottom: 1px solid {v['border_cell']};
    background: {v['bg_cell']};
    transition: background 0.15s;
    overflow: hidden;
}}
.cal-cell:hover {{ background: {'#1f1f35' if dark else '#fafafe'}; }}
.cal-cell.cal-empty {{ background: {v['bg_empty']}; }}
.cal-cell.cal-weekend {{ background: {v['bg_weekend']}; }}
.cal-cell.cal-today {{
    background: {v['bg_today']};
    border-top: 3px solid {v['today_accent']};
}}
.cal-day-num {{
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    font-weight: 500;
    color: {v['text_day']};
    margin-bottom: 6px;
    width: 26px; height: 26px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%;
}}
.cal-day-today-num {{
    background: {v['today_num_bg']};
    color: #ffffff !important;
    font-weight: 600;
}}
.cal-weekend .cal-day-num {{ color: {'#7060a8' if dark else '#9c8ab0'}; }}
.cal-tasks-wrap {{ display: flex; flex-direction: column; gap: 4px; }}
.cal-task {{
    font-size: 11px;
    font-weight: 500;
    padding: 3px 6px;
    border-radius: 5px;
    line-height: 1.35;
    cursor: default;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: transform 0.1s;
}}
.cal-task:hover {{ transform: scale(1.01); }}
.cal-more {{
    font-size: 11px;
    color: {v['text_more']};
    padding: 2px 4px;
    font-weight: 500;
}}
"""

    legend_dots = (
        '<div class="cal-legend-item">'
        '<div class="cal-legend-dot" style="background:#43a047;"></div>Baja</div>'
        '<div class="cal-legend-item">'
        '<div class="cal-legend-dot" style="background:#fb8c00;"></div>Media</div>'
        '<div class="cal-legend-item">'
        '<div class="cal-legend-dot" style="background:#e53935;"></div>Alta</div>'
    )
    days_row = "".join(f"<div>{d}</div>" for d in DAYS_HEADER)

    html = f"""
<style>{css}</style>
<div class="cronograma-root">
  <div class="cal-header">
    <div class="cal-month-title">{MONTH_NAMES_ES[month]}</div>
    <div style="display:flex;align-items:center;gap:16px;">
      <div class="cal-legend">{legend_dots}</div>
      <div class="cal-year-badge">{year}</div>
    </div>
  </div>
  <div class="cal-grid-wrap">
    <div class="cal-days-header">{days_row}</div>
    <div class="cal-grid">{day_cells_html}</div>
  </div>
</div>
"""
    return html


# ─────────────────────────────────────────────────────────────
#  Main page
# ─────────────────────────────────────────────────────────────

def admin_radmin_cronograma():
    _ensure_table()

    # ── Session state defaults ────────────────────────────────
    today = date.today()
    if "cal_year"  not in st.session_state: st.session_state.cal_year  = today.year
    if "cal_month" not in st.session_state: st.session_state.cal_month = today.month
    if "dark_mode" not in st.session_state: st.session_state.dark_mode = False

    dark = st.session_state.dark_mode

    # ── Page-level style injection ────────────────────────────
    if dark:
        page_css = """
        <style>
        section[data-testid="stMain"] > div { background: #0d0d1a !important; }
        .cronograma-page-title { color: #e8e8ff !important; }
        .cronograma-page-sub   { color: #6060a0 !important; }
        </style>
        """
    else:
        page_css = """
        <style>
        .cronograma-page-title { color: #1a1a2e; }
        .cronograma-page-sub   { color: #888; }
        </style>
        """

    st.markdown(page_css, unsafe_allow_html=True)

    # ── Header row ────────────────────────────────────────────
    h1, h2 = st.columns([8, 1])
    with h1:
        st.markdown(
            '<div class="cronograma-page-title" style="font-size:30px;font-weight:700;'
            'letter-spacing:-0.5px;margin-bottom:2px;">📋 Cronograma</div>'
            '<div class="cronograma-page-sub" style="font-size:14px;margin-bottom:8px;">'
            'Planifica y visualiza tus tareas por mes</div>',
            unsafe_allow_html=True,
        )
    with h2:
        moon = "🌙" if not dark else "☀️"
        label = f"{moon} {'Dark' if not dark else 'Light'}"
        if st.button(label, use_container_width=True):
            st.session_state.dark_mode = not dark
            st.rerun()

    # ── Month navigation ──────────────────────────────────────
    n1, n2, _, n3 = st.columns([1, 1, 4, 1])
    with n1:
        if st.button("◀ Anterior", use_container_width=True):
            m, y = st.session_state.cal_month - 1, st.session_state.cal_year
            if m < 1: m, y = 12, y - 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
    with n2:
        if st.button("Hoy", use_container_width=True):
            st.session_state.cal_year, st.session_state.cal_month = today.year, today.month
    with n3:
        if st.button("Siguiente ▶", use_container_width=True):
            m, y = st.session_state.cal_month + 1, st.session_state.cal_year
            if m > 12: m, y = 1, y + 1
            st.session_state.cal_month, st.session_state.cal_year = m, y

    st.divider()

    # ── Forms ─────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["✏️  Carga Manual", "📂  Carga por Archivo"])

    with tab1:
        with st.form("radmin_cronograma_manual"):
            c1, c2 = st.columns(2)
            with c1:
                tarea         = st.text_input("Tarea planificada *")
                fecha_objetivo = st.date_input("Fecha objetivo *", value=today, format="DD/MM/YYYY")
            with c2:
                prioridad = st.number_input("Prioridad (1-10)", min_value=1, max_value=10, value=1, step=1)
                notas     = st.text_area("Notas")
            archivo = st.file_uploader(
                "Archivo de soporte (opcional)",
                type=["pdf", "xlsx", "xls", "csv", "png", "jpg", "jpeg"],
                key="file_manual_radmin",
            )
            if st.form_submit_button("💾  Guardar en cronograma", use_container_width=True):
                if not tarea.strip():
                    st.error("La tarea es obligatoria.")
                else:
                    _insert_item(
                        tarea.strip(), fecha_objetivo, int(prioridad),
                        notas.strip() if notas else None,
                        archivo.name if archivo else None,
                        archivo.getvalue() if archivo else None,
                    )
                    st.success("✅ Guardado en cronograma.")
                    st.rerun()

    with tab2:
        st.markdown("Sube un `CSV` o `Excel` con columnas: `tarea_planeada`, `fecha_objetivo`, `prioridad` (opcional), `notas` (opcional).")
        archivo_tabla = st.file_uploader("Archivo masivo", type=["csv", "xlsx", "xls"], key="file_bulk_radmin")
        if archivo_tabla is not None:
            try:
                df = pd.read_csv(archivo_tabla) if archivo_tabla.name.lower().endswith(".csv") else pd.read_excel(archivo_tabla)
                df.columns = [str(c).strip().lower() for c in df.columns]
                if "tarea_planeada" not in df.columns or "fecha_objetivo" not in df.columns:
                    st.error("Faltan columnas obligatorias: tarea_planeada y fecha_objetivo.")
                else:
                    st.dataframe(df.head(20), use_container_width=True)
                    if st.button("⬆️  Importar al cronograma", use_container_width=True):
                        inserted = 0
                        for _, row in df.iterrows():
                            tarea = str(row.get("tarea_planeada", "")).strip()
                            if not tarea: continue
                            fecha = pd.to_datetime(row.get("fecha_objetivo"), errors="coerce")
                            if pd.isna(fecha): continue
                            prio = row.get("prioridad", 1)
                            try: prio = int(prio)
                            except: prio = 1
                            notas = row.get("notas", None)
                            notas = str(notas).strip() if pd.notna(notas) else None
                            _insert_item(tarea, fecha.date(), max(1, min(10, prio)), notas, archivo_tabla.name, None)
                            inserted += 1
                        st.success(f"✅ Importación completada: {inserted} registros.")
                        st.rerun()
            except Exception as ex:
                st.error(f"No se pudo procesar el archivo: {ex}")

    st.divider()

    # ── Metrics ───────────────────────────────────────────────
    rows = _list_items()
    year  = st.session_state.cal_year
    month = st.session_state.cal_month

    month_tasks = [
        r for r in rows
        if getattr(r["fecha_objetivo"], "year",  None) == year
        and getattr(r["fecha_objetivo"], "month", None) == month
    ]

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Total del mes",    len(month_tasks))
    sc2.metric("Alta prioridad",   sum(1 for r in month_tasks if r["prioridad"] >= 7))
    sc3.metric("Pendientes",       sum(1 for r in month_tasks if r["estado"] == "pendiente_plan"))
    sc4.metric("Total histórico",  len(rows))

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Calendar ──────────────────────────────────────────────
    cal_html = _render_calendar_html(rows, year, month, dark)
    st.html(cal_html)

    st.divider()

    # ── Task list for current month ───────────────────────────
    st.markdown("### Tareas del mes")
    if not month_tasks:
        st.info("No hay tareas para este mes.")
    else:
        for r in month_tasks:
            ps = _get_prioridad_style(r["prioridad"], dark)
            es = _get_estado_style(r["estado"], dark)
            fecha_txt = (
                r["fecha_objetivo"].strftime("%d/%m/%Y")
                if hasattr(r["fecha_objetivo"], "strftime")
                else str(r["fecha_objetivo"])
            )
            with st.container(border=True):
                c1, c2 = st.columns([7, 1])
                with c1:
                    st.markdown(
                        f"<span style='background:{ps['bg']};color:{ps['text']};"
                        f"border-left:3px solid {ps['border']};padding:2px 8px;"
                        f"border-radius:4px;font-size:12px;font-weight:600;'>"
                        f"P{r['prioridad']} · {ps['label']}</span>&nbsp;&nbsp;"
                        f"<span style='background:{es['bg']};color:{es['text']};"
                        f"padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;'>"
                        f"{es['label']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"**#{r['id']} · {r['tarea_planeada']}**  \n"
                        f"📅 `{fecha_txt}`"
                        + (f"  \n📝 {r['notas']}" if r["notas"] else "")
                        + (f"  \n📎 `{r['archivo_nombre']}`" if r["archivo_nombre"] else "")
                    )
                with c2:
                    if st.button("🗑️", key=f"del_radmin_{r['id']}",
                                 use_container_width=True, help="Eliminar tarea"):
                        _delete_item(r["id"])
                        st.rerun()