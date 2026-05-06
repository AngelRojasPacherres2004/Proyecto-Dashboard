import streamlit as st
import pandas as pd
import calendar
import re
import hashlib
from datetime import date
from config.db import get_connection
from pypdf import PdfReader


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
            empresa_id BIGINT NULL REFERENCES empresas(id),
            tipo_tarea TEXT NOT NULL DEFAULT 'PLAME',
            mes_vencimiento SMALLINT NOT NULL DEFAULT 1,
            ruc_ultimo_digito SMALLINT NULL,
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
    cur.execute("ALTER TABLE radmin_cronograma ADD COLUMN IF NOT EXISTS empresa_id BIGINT NULL REFERENCES empresas(id)")
    cur.execute("ALTER TABLE radmin_cronograma ADD COLUMN IF NOT EXISTS tipo_tarea TEXT NOT NULL DEFAULT 'PLAME'")
    cur.execute("ALTER TABLE radmin_cronograma ADD COLUMN IF NOT EXISTS mes_vencimiento SMALLINT NOT NULL DEFAULT 1")
    cur.execute("ALTER TABLE radmin_cronograma ADD COLUMN IF NOT EXISTS ruc_ultimo_digito SMALLINT NULL")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS radmin_vencimientos (
            id BIGSERIAL PRIMARY KEY,
            tipo_tarea TEXT NOT NULL,
            mes SMALLINT NOT NULL,
            ruc_ultimo_digito SMALLINT NOT NULL,
            dia_vencimiento SMALLINT NOT NULL,
            pdf_nombre TEXT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (tipo_tarea, mes, ruc_ultimo_digito)
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def _insert_item(tarea, fecha_objetivo, prioridad, notas=None,
                 empresa_id=None, tipo_tarea="PLAME", mes_vencimiento=1, ruc_ultimo_digito=None,
                 archivo_nombre=None, archivo_data=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO radmin_cronograma
        (empresa_id, tipo_tarea, mes_vencimiento, ruc_ultimo_digito, tarea_planeada, fecha_objetivo, prioridad, notas, archivo_nombre, archivo_data, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendiente_plan')
        """,
        (empresa_id, tipo_tarea, mes_vencimiento, ruc_ultimo_digito, tarea, fecha_objetivo, prioridad, notas, archivo_nombre, archivo_data),
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
               archivo_nombre, estado, created_at, tipo_tarea, empresa_id, mes_vencimiento, ruc_ultimo_digito
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


def _delete_all_tareas(tipo_tarea: str = None):
    conn = get_connection()
    cur = conn.cursor()
    if tipo_tarea:
        cur.execute("DELETE FROM radmin_cronograma WHERE tipo_tarea = %s", (tipo_tarea,))
    else:
        cur.execute("DELETE FROM radmin_cronograma")
    conn.commit()
    cur.close()
    conn.close()


def _get_empresas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, razon_social, alias, ruc FROM empresas ORDER BY razon_social")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def _save_vencimiento(tipo_tarea: str, mes: int, digito: int, dia: int, pdf_nombre: str = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO radmin_vencimientos (tipo_tarea, mes, ruc_ultimo_digito, dia_vencimiento, pdf_nombre)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (tipo_tarea, mes, ruc_ultimo_digito)
        DO UPDATE SET dia_vencimiento = EXCLUDED.dia_vencimiento, pdf_nombre = EXCLUDED.pdf_nombre
        """,
        (tipo_tarea, mes, digito, dia, pdf_nombre),
    )
    conn.commit()
    cur.close()
    conn.close()


def _get_dia_vencimiento(tipo_tarea: str, mes: int, digito: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT dia_vencimiento
        FROM radmin_vencimientos
        WHERE tipo_tarea = %s AND mes = %s AND ruc_ultimo_digito = %s
        LIMIT 1
        """,
        (tipo_tarea, mes, digito),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["dia_vencimiento"] if row else None


def _get_all_vencimientos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT tipo_tarea, mes, ruc_ultimo_digito, dia_vencimiento, pdf_nombre
        FROM radmin_vencimientos
        ORDER BY tipo_tarea, mes, ruc_ultimo_digito
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def _delete_vencimiento(tipo_tarea: str, mes: int, digito: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM radmin_vencimientos WHERE tipo_tarea = %s AND mes = %s AND ruc_ultimo_digito = %s",
        (tipo_tarea, mes, digito),
    )
    conn.commit()
    cur.close()
    conn.close()


def _parse_vencimientos_pdf(pdf_file):
    """Extrae las fechas del PDF de SUNAT de forma precisa"""
    text = ""
    reader = PdfReader(pdf_file)
    for pg in reader.pages:
        text += (pg.extract_text() or "") + "\n"
    
    meses = {
        "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
        "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12,
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12
    }
    
    rules = []
    lines = text.split('\n')
    
    for line in lines:
        for nombre_mes, num_mes in meses.items():
            if nombre_mes.lower() in line.lower():
                año_match = re.search(r'\b(20\d{2})\b', line)
                año = int(año_match.group(1)) if año_match else 2026
                numeros = re.findall(r'\b([12]?\d|3[01])\b', line)
                dias = [int(n) for n in numeros if 1 <= int(n) <= 31]
                grupos = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
                for idx, (g1, g2) in enumerate(grupos):
                    if idx < len(dias):
                        dia = dias[idx]
                        rules.append((num_mes, g1, dia, año))
                        rules.append((num_mes, g2, dia, año))
                break
    
    rules = list(set(rules))
    rules.sort(key=lambda x: (x[0], x[1]))
    return rules


def _generar_tareas_para_empresas(tipo_tarea: str, año: int = None):
    """Genera tareas automáticas para todas las empresas según las reglas cargadas"""
    if año is None:
        año = date.today().year
    
    reglas = _get_all_vencimientos()
    reglas = [r for r in reglas if r["tipo_tarea"] == tipo_tarea]
    if not reglas:
        return 0
    
    empresas = _get_empresas()
    tareas_creadas = 0
    for empresa in empresas:
        ruc = str(empresa.get("ruc", "")).strip()
        if not ruc or not ruc[-1].isdigit():
            continue
        digito = int(ruc[-1])
        for regla in reglas:
            mes = regla["mes"]
            dia = regla["dia_vencimiento"]
            try:
                fecha_obj = date(año, mes, dia)
            except ValueError:
                continue
            # Verificar si ya existe tarea para esta empresa, mes y tipo
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM radmin_cronograma WHERE empresa_id = %s AND tipo_tarea = %s AND mes_vencimiento = %s AND fecha_objetivo = %s",
                (empresa["id"], tipo_tarea, mes, fecha_obj)
            )
            existe = cur.fetchone()
            cur.close()
            conn.close()
            if not existe:
                nombre_tarea = f"{tipo_tarea} - {empresa['razon_social']}"
                _insert_item(
                    tarea=nombre_tarea,
                    fecha_objetivo=fecha_obj,
                    prioridad=7,
                    notas=f"Vencimiento {tipo_tarea} - {fecha_obj.strftime('%d/%m/%Y')} - RUC termina en {digito}",
                    empresa_id=empresa["id"],
                    tipo_tarea=tipo_tarea,
                    mes_vencimiento=mes,
                    ruc_ultimo_digito=digito,
                )
                tareas_creadas += 1
    return tareas_creadas


# ─────────────────────────────────────────────────────────────
#  Color helper para tareas (colores únicos por tarea)
# ─────────────────────────────────────────────────────────────

def _get_task_color(task_id: int, task_name: str) -> str:
    key = str(task_id) if task_id else task_name
    hash_val = int(hashlib.md5(key.encode()).hexdigest()[:8], 16)
    hue = hash_val % 360
    saturation = 55 + (hash_val % 30)
    lightness = 45 + (hash_val % 20)
    return f"hsl({hue}, {saturation}%, {lightness}%)"


def _get_contrast_text_color(bg_hsl: str) -> str:
    match = re.search(r'hsl\([\d.]+, [\d.]+%, ([\d.]+)%', bg_hsl)
    if match:
        lightness = float(match.group(1))
        return "#ffffff" if lightness < 60 else "#1a1a2e"
    return "#ffffff"


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
            is_today = current_date == today
            is_weekend = current_date.weekday() >= 5
            day_tasks = tasks_by_date.get(current_date, [])

            cell_class = "cal-cell"
            if is_today:
                cell_class += " cal-today"
            elif is_weekend:
                cell_class += " cal-weekend"

            tasks_html = ""
            for t in day_tasks[:5]:
                bg_color = _get_task_color(t["id"], t["tarea_planeada"])
                text_color = _get_contrast_text_color(bg_color)
                name = t["tarea_planeada"]
                name = name[:20] + "…" if len(name) > 20 else name
                tasks_html += (
                    f'<div class="cal-task" style="'
                    f'background:{bg_color};'
                    f'color:{text_color};'
                    f'border-radius:6px;'
                    f'padding:4px 6px;'
                    f'margin-bottom:3px;'
                    f'font-size:11px;'
                    f'font-weight:500;'
                    f'white-space:nowrap;'
                    f'overflow:hidden;'
                    f'text-overflow:ellipsis;'
                    f'cursor:default;">'
                    f'{name}</div>'
                )
            if len(day_tasks) > 5:
                tasks_html += f'<div class="cal-more">+{len(day_tasks)-5} más</div>'

            num_class = "cal-day-num"
            if is_today:
                num_class += " cal-day-today-num"

            day_cells_html += (
                f'<div class="{cell_class}">'
                f'<div class="{num_class}">{day_num}</div>'
                f'<div class="cal-tasks-wrap">{tasks_html}</div>'
                f'</div>'
            )

    # Estilos CSS según modo oscuro/claro
    if dark:
        v = {
            "bg_page": "transparent", "bg_grid": "#13131f", "bg_cell": "#1a1a2e",
            "bg_empty": "#111120", "bg_weekend": "#1e1830", "bg_today": "#0e1540",
            "border_cell": "#252540", "text_month": "#e8e8ff", "text_day": "#9090b8",
            "text_more": "#6060a0", "header_bg": "#0d0d1a", "header_text": "rgba(246,194,125,0.9)",
            "header_wknd": "rgba(246,194,125,0.4)", "badge_bg": "#0d0d1a", "badge_text": "#f6c27d",
            "today_accent": "#5c7cfa", "today_num_bg": "#3d5afe",
        }
    else:
        v = {
            "bg_page": "transparent", "bg_grid": "#ffffff", "bg_cell": "#ffffff",
            "bg_empty": "#f8f8fc", "bg_weekend": "#fdf8ff", "bg_today": "#f0f4ff",
            "border_cell": "#ebebf5", "text_month": "#1a1a2e", "text_day": "#5a5a7a",
            "text_more": "#9090b0", "header_bg": "#1a1a2e", "header_text": "rgba(246,194,125,0.85)",
            "header_wknd": "rgba(246,194,125,0.4)", "badge_bg": "#1a1a2e", "badge_text": "#f6c27d",
            "today_accent": "#3d5afe", "today_num_bg": "#3d5afe",
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
    flex-wrap: wrap;
    gap: 12px;
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
    overflow-y: auto;
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
    transition: transform 0.1s, opacity 0.1s;
}}
.cal-task:hover {{
    transform: scale(1.02);
    opacity: 0.95;
}}
.cal-more {{
    font-size: 10px;
    color: {v['text_more']};
    padding: 2px 4px;
    font-weight: 500;
}}
"""

    days_row = "".join(f"<div>{d}</div>" for d in DAYS_HEADER)

    html = f"""
<style>{css}</style>
<div class="cronograma-root">
  <div class="cal-header">
    <div class="cal-month-title">{MONTH_NAMES_ES[month]}</div>
    <div class="cal-year-badge">{year}</div>
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

    today = date.today()
    if "cal_year" not in st.session_state:
        st.session_state.cal_year = today.year
    if "cal_month" not in st.session_state:
        st.session_state.cal_month = today.month
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    dark = st.session_state.dark_mode

    # Estilos de página
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

    # Header
    h1, h2 = st.columns([8, 1])
    with h1:
        st.markdown(
            '<div class="cronograma-page-title" style="font-size:30px;font-weight:700;'
            'letter-spacing:-0.5px;margin-bottom:2px;">📋 Cronograma Tributario</div>'
            '<div class="cronograma-page-sub" style="font-size:14px;margin-bottom:8px;">'
            'Vencimientos PLAME y DJ según último dígito del RUC</div>',
            unsafe_allow_html=True,
        )
    with h2:
        moon = "🌙" if not dark else "☀️"
        label = f"{moon} {'Dark' if not dark else 'Light'}"
        if st.button(label, use_container_width=True):
            st.session_state.dark_mode = not dark
            st.rerun()

    # Navegación de mes
    n1, n2, _, n3 = st.columns([1, 1, 4, 1])
    with n1:
        if st.button("◀ Anterior", use_container_width=True):
            m, y = st.session_state.cal_month - 1, st.session_state.cal_year
            if m < 1:
                m, y = 12, y - 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
    with n2:
        if st.button("Hoy", use_container_width=True):
            st.session_state.cal_year, st.session_state.cal_month = today.year, today.month
    with n3:
        if st.button("Siguiente ▶", use_container_width=True):
            m, y = st.session_state.cal_month + 1, st.session_state.cal_year
            if m > 12:
                m, y = 1, y + 1
            st.session_state.cal_month, st.session_state.cal_year = m, y

    st.divider()

    tipo_filtro = st.selectbox("📌 Mostrar tareas de", ["PLAME", "DJ"], index=0)

    # Panel de configuración de vencimientos (visible)
    with st.expander("📄 Configuración de vencimientos (reglas desde PDF)", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            tipo_pdf = st.selectbox("Tipo de calendario", ["PLAME", "DJ"], key="tipo_pdf_venc")
            pdf_venc = st.file_uploader("📎 Subir PDF de fechas SUNAT", type=["pdf"], key="pdf_venc_upload")
            if st.button("📤 1. Cargar reglas desde PDF", use_container_width=True):
                if pdf_venc is None:
                    st.error("❌ Sube un PDF primero.")
                else:
                    try:
                        reglas = _parse_vencimientos_pdf(pdf_venc)
                        if not reglas:
                            st.error("⚠️ No se detectaron reglas. Verifica el formato.")
                        else:
                            for mes, dig, dia, año in reglas:
                                _save_vencimiento(tipo_pdf, mes, dig, dia, pdf_venc.name)
                            st.success(f"✅ Cargadas {len(reglas)} reglas")
                            st.rerun()
                    except Exception as ex:
                        st.error(f"❌ Error: {ex}")
        with col2:
            año_generar = st.number_input("Año para generar tareas", min_value=2024, max_value=2030, value=today.year)
            if st.button("🎯 2. Generar tareas automáticas", use_container_width=True):
                reglas_existentes = _get_all_vencimientos()
                if not [r for r in reglas_existentes if r["tipo_tarea"] == tipo_filtro]:
                    st.warning(f"⚠️ No hay reglas para {tipo_filtro}. Carga el PDF primero.")
                else:
                    tareas_creadas = _generar_tareas_para_empresas(tipo_filtro, año_generar)
                    if tareas_creadas > 0:
                        st.success(f"✅ Generadas {tareas_creadas} tareas para {tipo_filtro}")
                        st.rerun()
                    else:
                        st.info("ℹ️ No se generaron tareas nuevas (ya existen o no hay empresas con RUC).")
            if st.button("🗑️ Limpiar todas las tareas", use_container_width=True):
                _delete_all_tareas(tipo_filtro)
                st.success(f"✅ Eliminadas todas las tareas de {tipo_filtro}")
                st.rerun()

        # Mostrar las reglas actualmente cargadas en una tabla
        reglas_actuales = _get_all_vencimientos()
        if reglas_actuales:
            st.markdown("---")
            st.markdown("**📋 Reglas de vencimiento cargadas actualmente:**")
            df_reglas = pd.DataFrame(reglas_actuales)
            df_reglas = df_reglas.rename(columns={
                "tipo_tarea": "Tipo", "mes": "Mes", "ruc_ultimo_digito": "Dígito RUC", "dia_vencimiento": "Día"
            })
            df_reglas["Mes"] = df_reglas["Mes"].apply(lambda x: MONTH_NAMES_ES[x])
            st.dataframe(df_reglas, use_container_width=True, hide_index=True)

    st.divider()

    # Obtener tareas desde la BD
    rows = _list_items()
    year = st.session_state.cal_year
    month = st.session_state.cal_month

    # Filtrar tareas del mes y tipo seleccionado
    month_tasks = [
        r for r in rows
        if hasattr(r["fecha_objetivo"], "year") and r["fecha_objetivo"].year == year
        and r["fecha_objetivo"].month == month and r.get("tipo_tarea") == tipo_filtro
    ]

    # Métricas
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric(f"📌 Tareas {tipo_filtro} este mes", len(month_tasks))
    col_m2.metric("🔥 Alta prioridad (7-10)", sum(1 for r in month_tasks if r["prioridad"] >= 7))
    col_m3.metric("⏳ Pendientes", sum(1 for r in month_tasks if r["estado"] == "pendiente_plan"))
    col_m4.metric("📊 Total general", len(rows))

    st.markdown(f"### 📅 Calendario de {tipo_filtro} - {MONTH_NAMES_ES[month]} {year}")
    cal_html = _render_calendar_html(month_tasks, year, month, dark)
    st.html(cal_html)

    st.divider()

    # Lista detallada de tareas del mes
    st.markdown(f"### 📝 Lista de tareas - {MONTH_NAMES_ES[month]} {year}")
    if not month_tasks:
        st.info("No hay tareas para este mes. Utiliza el panel de configuración para cargar reglas y generar tareas automáticas.")
    else:
        for r in month_tasks:
            fecha_txt = r["fecha_objetivo"].strftime("%d/%m/%Y") if hasattr(r["fecha_objetivo"], "strftime") else str(r["fecha_objetivo"])
            with st.container(border=True):
                col_t1, col_t2 = st.columns([7, 1])
                with col_t1:
                    st.markdown(f"**📌 {r['tarea_planeada']}**  \n📅 Vence: `{fecha_txt}`")
                    if r["notas"]:
                        st.caption(f"📝 {r['notas']}")
                with col_t2:
                    if st.button("🗑️", key=f"del_{r['id']}", use_container_width=True):
                        _delete_item(r["id"])
                        st.rerun()