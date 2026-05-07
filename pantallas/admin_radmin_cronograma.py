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


def _get_tareas_por_empresa(empresa_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, tarea_planeada, fecha_objetivo, prioridad, notas, tipo_tarea, mes_vencimiento, estado
        FROM radmin_cronograma
        WHERE empresa_id = %s
        ORDER BY fecha_objetivo ASC
        """,
        (empresa_id,)
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


def _get_empresa_by_id(empresa_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, razon_social, alias, ruc FROM empresas WHERE id = %s", (empresa_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


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


def _delete_all_vencimientos(tipo_tarea: str = None):
    """Elimina todas las reglas de vencimiento (opcionalmente filtradas por tipo)"""
    conn = get_connection()
    cur = conn.cursor()
    if tipo_tarea:
        cur.execute("DELETE FROM radmin_vencimientos WHERE tipo_tarea = %s", (tipo_tarea,))
    else:
        cur.execute("DELETE FROM radmin_vencimientos")
    conn.commit()
    cur.close()
    conn.close()


def _parse_vencimientos_pdf(pdf_file):
    """
    Parser exacto para el Cronograma SUNAT.
    
    El PDF extrae el texto con día y mes en líneas separadas, ej:
      "Ene-2026 16\\nFeb\\n17\\nFeb\\n18\\nFeb\\n19\\nFeb\\n20\\nFeb\\n23\\nFeb\\n24\\nFeb"
    
    Estructura columnas: dígito 0 | dígito 1 | 2y3 | 4y5 | 6y7 | 8y9 | buenos contrib (ignorado)
    """
    text = ""
    reader = PdfReader(pdf_file)
    for pg in reader.pages:
        text += (pg.extract_text() or "") + "\n"

    # Normalizar: pasar todo a una sola línea para facilitar el regex
    text_flat = text.replace('\n', ' ')

    MES_NUM = {
        "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
        "jul": 7, "ago": 8, "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    }

    # Columna 0→dígito 0, col 1→dígito 1, col 2→dígitos 2y3,
    # col 3→dígitos 4y5, col 4→dígitos 6y7, col 5→dígitos 8y9
    # (col 6 = buenos contribuyentes, se ignora)
    DIGITOS_POR_COL = [[0], [1], [2, 3], [4, 5], [6, 7], [8, 9]]

    # Buscar bloques: "Ene-2026" o "Ene 2026" seguido de 6+ pares (número mes_abrev)
    PERIODO_RE = re.compile(
        r'([A-Za-záéíóúÁÉÍÓÚ]{3,4})[.\-\s]*(20\d{2})\s+'
        r'((?:\d{1,2}\s+[A-Za-záéíóúÁÉÍÓÚ]{2,3}\s*){6,7})',
        re.IGNORECASE
    )

    rules = []
    for m in PERIODO_RE.finditer(text_flat):
        año = int(m.group(2))
        pairs = re.findall(r'(\d{1,2})\s+([A-Za-záéíóúÁÉÍÓÚ]{2,3})', m.group(3))
        # Tomar solo las primeras 6 columnas (ignorar col 7 = buenos contribuyentes)
        for col_idx, digitos in enumerate(DIGITOS_POR_COL):
            if col_idx >= len(pairs):
                break
            dia_str, mes_str = pairs[col_idx]
            dia = int(dia_str)
            mes_num = MES_NUM.get(mes_str[:3].lower())
            if mes_num and 1 <= dia <= 31:
                for d in digitos:
                    rules.append((mes_num, d, dia, año))

    rules = list(set(rules))
    rules.sort(key=lambda x: (x[0], x[1]))
    return rules


def _generar_tareas_para_empresas(tipo_tarea: str, año: int = None):
    """
    Genera una tarea por empresa, por mes, para el tipo de tarea (PLAME/DJ)
    según las reglas de vencimiento cargadas desde el PDF.
    Coloca cada empresa en la fecha correspondiente según el último dígito del RUC.
    """
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

        # Buscar reglas que aplican al dígito de esta empresa
        reglas_empresa = [r for r in reglas if r["ruc_ultimo_digito"] == digito]

        for regla in reglas_empresa:
            mes = regla["mes"]
            dia = regla["dia_vencimiento"]
            try:
                fecha_obj = date(año, mes, dia)
            except ValueError:
                continue

            # Verificar si ya existe esta tarea para evitar duplicados
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id FROM radmin_cronograma
                WHERE empresa_id = %s AND tipo_tarea = %s
                  AND mes_vencimiento = %s AND fecha_objetivo = %s
                """,
                (empresa["id"], tipo_tarea, mes, fecha_obj)
            )
            existe = cur.fetchone()
            cur.close()
            conn.close()

            if not existe:
                # El nombre en el calendario es la razón social (o alias si es más corto)
                alias = empresa.get("alias") or ""
                nombre_display = alias if alias and len(alias) <= 20 else empresa["razon_social"]
                nombre_tarea = nombre_display

                _insert_item(
                    tarea=nombre_tarea,
                    fecha_objetivo=fecha_obj,
                    prioridad=7,
                    notas=(
                        f"Empresa: {empresa['razon_social']} | "
                        f"RUC: {ruc} (termina en {digito}) | "
                        f"Tipo: {tipo_tarea} | "
                        f"Vencimiento: {fecha_obj.strftime('%d/%m/%Y')}"
                    ),
                    empresa_id=empresa["id"],
                    tipo_tarea=tipo_tarea,
                    mes_vencimiento=mes,
                    ruc_ultimo_digito=digito,
                )
                tareas_creadas += 1

    return tareas_creadas


# ─────────────────────────────────────────────────────────────
#  Color helper para empresas (colores únicos por empresa)
# ─────────────────────────────────────────────────────────────

def _get_empresa_color(empresa_id: int) -> str:
    hash_val = int(hashlib.md5(str(empresa_id).encode()).hexdigest()[:8], 16)
    hue = hash_val % 360
    saturation = 55 + (hash_val % 30)
    lightness = 50 + (hash_val % 15)
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
            for t in day_tasks:
                empresa_id = t.get("empresa_id")
                if empresa_id:
                    bg_color = _get_empresa_color(empresa_id)
                else:
                    bg_color = "#888888"
                text_color = _get_contrast_text_color(bg_color)

                # Mostrar alias o nombre corto en el calendario
                name = t["tarea_planeada"]
                name_short = name[:18] + "…" if len(name) > 18 else name
                tipo = t.get("tipo_tarea", "")
                fecha_str = t["fecha_objetivo"].strftime("%d/%m/%Y") if hasattr(t["fecha_objetivo"], "strftime") else str(t["fecha_objetivo"])

                tasks_html += (
                    f'<div class="cal-task" style="'
                    f'background:{bg_color};'
                    f'color:{text_color};'
                    f'" title="{name} | {tipo} | vence {fecha_str}">'
                    f'<span class="cal-task-tipo">{tipo}</span>'
                    f'{name_short}'
                    f'</div>'
                )

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
    min-height: 120px;
    max-height: 220px;
    padding: 8px 6px 6px;
    border-right: 1px solid {v['border_cell']};
    border-bottom: 1px solid {v['border_cell']};
    background: {v['bg_cell']};
    transition: background 0.15s;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: thin;
    scrollbar-color: {v['border_cell']} transparent;
}}
.cal-cell::-webkit-scrollbar {{ width: 3px; }}
.cal-cell::-webkit-scrollbar-track {{ background: transparent; }}
.cal-cell::-webkit-scrollbar-thumb {{ background: {v['border_cell']}; border-radius: 2px; }}
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
.cal-tasks-wrap {{ display: flex; flex-direction: column; gap: 3px; }}
.cal-task {{
    border-radius: 6px;
    padding: 3px 6px;
    font-size: 11px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    cursor: pointer;
    transition: transform 0.1s, opacity 0.1s;
    display: flex;
    align-items: center;
    gap: 4px;
}}
.cal-task:hover {{
    transform: scale(1.02);
    opacity: 0.9;
}}
.cal-task-tipo {{
    font-size: 9px;
    font-weight: 700;
    opacity: 0.75;
    letter-spacing: 0.5px;
    flex-shrink: 0;
    background: rgba(0,0,0,0.15);
    border-radius: 3px;
    padding: 1px 3px;
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
    if "selected_empresa_id" not in st.session_state:
        st.session_state.selected_empresa_id = None

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

    # ── Header ──────────────────────────────────────────────
    h1, h2 = st.columns([8, 1])
    with h1:
        st.markdown(
            '<div class="cronograma-page-title" style="font-size:30px;font-weight:700;'
            'letter-spacing:-0.5px;margin-bottom:2px;">📋 Cronograma Tributario</div>'
            '<div class="cronograma-page-sub" style="font-size:14px;margin-bottom:8px;">'
            'Empresas ubicadas en el calendario según su RUC y fecha de vencimiento SUNAT</div>',
            unsafe_allow_html=True,
        )
    with h2:
        moon = "🌙" if not dark else "☀️"
        label = f"{moon} {'Dark' if not dark else 'Light'}"
        if st.button(label, use_container_width=True):
            st.session_state.dark_mode = not dark
            st.rerun()

    # ── Panel PDF ────────────────────────────────────────────
    with st.expander("📄 Cargar calendario SUNAT desde PDF", expanded=not bool(_get_all_vencimientos())):
        st.markdown(
            "Al subir el PDF, las empresas se colocarán **automáticamente** en el calendario "
            "según el último dígito de su RUC y las fechas de vencimiento del PDF."
        )
        col_pdf1, col_pdf2 = st.columns(2)
        with col_pdf1:
            tipo_pdf = st.selectbox("Tipo de calendario", ["PLAME", "DJ"], key="tipo_pdf_venc")
            año_pdf = st.number_input(
                "Año", min_value=2024, max_value=2030,
                value=today.year, key="año_pdf"
            )
        with col_pdf2:
            pdf_venc = st.file_uploader(
                "📎 Subir PDF de fechas SUNAT",
                type=["pdf"],
                key="pdf_venc_upload"
            )

        if pdf_venc is not None:
            if st.button("⚡ Cargar PDF y ubicar empresas en el calendario", use_container_width=True, type="primary"):
                with st.spinner("Leyendo PDF y generando cronograma..."):
                    try:
                        # 1. Parsear reglas del PDF
                        reglas = _parse_vencimientos_pdf(pdf_venc)
                        if not reglas:
                            st.error("⚠️ No se detectaron fechas en el PDF. Verifica el formato.")
                        else:
                            # Mostrar preview de lo que se leyó
                            st.markdown(f"**🔍 Vista previa — {len(reglas)} reglas detectadas en el PDF:**")
                            preview_data = []
                            for mes_v, dig, dia, año_v in sorted(reglas, key=lambda x: (x[0], x[1])):
                                preview_data.append({
                                    "Mes vencimiento": MONTH_NAMES_ES[mes_v],
                                    "Dígito RUC": dig,
                                    "Día": dia,
                                    "Año": año_v,
                                    "Fecha completa": f"{dia:02d}/{mes_v:02d}/{año_v}"
                                })
                            df_preview = pd.DataFrame(preview_data)
                            st.dataframe(df_preview, use_container_width=True, hide_index=True)

                            # 2. Guardar en BD
                            for mes_v, dig, dia, año_v in reglas:
                                _save_vencimiento(tipo_pdf, mes_v, dig, dia, pdf_venc.name)
                            st.success(f"✅ {len(reglas)} reglas guardadas del PDF «{pdf_venc.name}»")

                            # 3. Generar tareas automáticamente para todas las empresas
                            tareas_creadas = _generar_tareas_para_empresas(tipo_pdf, int(año_pdf))
                            if tareas_creadas > 0:
                                st.success(
                                    f"🎯 {tareas_creadas} entradas generadas — "
                                    f"empresas ubicadas en el calendario {tipo_pdf} {int(año_pdf)}"
                                )
                            else:
                                st.info(
                                    "ℹ️ No se generaron nuevas entradas "
                                    "(ya existen o no hay empresas con RUC registrado)."
                                )
                            st.rerun()
                    except Exception as ex:
                        st.error(f"❌ Error procesando el PDF: {ex}")

        # Mostrar reglas actuales cargadas
        reglas_actuales = _get_all_vencimientos()
        if reglas_actuales:
            st.markdown("---")

            col_reglas_title, col_borrar_todo = st.columns([5, 2])
            with col_reglas_title:
                st.markdown("**📋 Reglas de vencimiento cargadas:**")
            with col_borrar_todo:
                if st.button("🗑️ Borrar TODAS las reglas", use_container_width=True, type="secondary"):
                    _delete_all_vencimientos()
                    _delete_all_tareas()
                    st.success("✅ Todas las reglas y tareas han sido eliminadas")
                    st.rerun()

            df_reglas = pd.DataFrame(reglas_actuales)
            df_reglas = df_reglas.rename(columns={
                "tipo_tarea": "Tipo", "mes": "Mes",
                "ruc_ultimo_digito": "Último dígito RUC", "dia_vencimiento": "Día vencimiento",
                "pdf_nombre": "PDF"
            })
            df_reglas["Mes"] = df_reglas["Mes"].apply(lambda x: MONTH_NAMES_ES[x])
            st.dataframe(df_reglas[["Tipo", "Mes", "Último dígito RUC", "Día vencimiento", "PDF"]],
                         use_container_width=True, hide_index=True)

            st.markdown("**Borrar por tipo:**")
            col_limpiar1, col_limpiar2, col_limpiar3 = st.columns(3)
            with col_limpiar1:
                if st.button("🗑️ Reglas + tareas PLAME", use_container_width=True):
                    _delete_all_vencimientos("PLAME")
                    _delete_all_tareas("PLAME")
                    st.success("✅ Eliminado PLAME")
                    st.rerun()
            with col_limpiar2:
                if st.button("🗑️ Reglas + tareas DJ", use_container_width=True):
                    _delete_all_vencimientos("DJ")
                    _delete_all_tareas("DJ")
                    st.success("✅ Eliminado DJ")
                    st.rerun()
            with col_limpiar3:
                if st.button("🗑️ Solo tareas (mantener reglas)", use_container_width=True):
                    _delete_all_tareas()
                    st.success("✅ Tareas eliminadas, reglas conservadas")
                    st.rerun()

    st.divider()

    # ── Filtro y navegación con selectores desplegables ──────
    nav_col1, nav_col2, nav_col3 = st.columns([2, 1, 2])
    with nav_col1:
        tipo_filtro = st.selectbox(
            "📌 Tipo de tarea",
            ["PLAME", "DJ", "TODOS"],
            index=0,
            key="tipo_filtro_sel"
        )
    with nav_col2:
        mes_opciones = {
            MONTH_NAMES_ES[i]: i for i in range(1, 13)
        }
        mes_sel = st.selectbox(
            "📅 Mes",
            options=list(mes_opciones.keys()),
            index=st.session_state.cal_month - 1,
            key="mes_selector"
        )
        if mes_opciones[mes_sel] != st.session_state.cal_month:
            st.session_state.cal_month = mes_opciones[mes_sel]
            st.rerun()
    with nav_col3:
        año_sel = st.selectbox(
            "📆 Año",
            options=list(range(2024, 2031)),
            index=list(range(2024, 2031)).index(st.session_state.cal_year),
            key="año_selector"
        )
        if año_sel != st.session_state.cal_year:
            st.session_state.cal_year = año_sel
            st.rerun()

    # Botones de navegación rápida
    b1, b2, b3, b4 = st.columns([1, 1, 5, 1])
    with b1:
        if st.button("◀ Anterior", use_container_width=True):
            m, y = st.session_state.cal_month - 1, st.session_state.cal_year
            if m < 1:
                m, y = 12, y - 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
            st.rerun()
    with b2:
        if st.button("Hoy", use_container_width=True):
            st.session_state.cal_year, st.session_state.cal_month = today.year, today.month
            st.rerun()
    with b4:
        if st.button("Siguiente ▶", use_container_width=True):
            m, y = st.session_state.cal_month + 1, st.session_state.cal_year
            if m > 12:
                m, y = 1, y + 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
            st.rerun()

    # ── Obtener tareas ───────────────────────────────────────
    rows = _list_items()
    year = st.session_state.cal_year
    month = st.session_state.cal_month

    if tipo_filtro == "TODOS":
        month_tasks = [
            r for r in rows
            if hasattr(r["fecha_objetivo"], "year")
            and r["fecha_objetivo"].year == year
            and r["fecha_objetivo"].month == month
        ]
    else:
        month_tasks = [
            r for r in rows
            if hasattr(r["fecha_objetivo"], "year")
            and r["fecha_objetivo"].year == year
            and r["fecha_objetivo"].month == month
            and r.get("tipo_tarea") == tipo_filtro
        ]

    # ── Métricas ─────────────────────────────────────────────
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("🏢 Empresas este mes", len(set(r.get("empresa_id") for r in month_tasks if r.get("empresa_id"))))
    col_m2.metric("📌 Tareas este mes", len(month_tasks))
    col_m3.metric("⏳ Pendientes", sum(1 for r in month_tasks if r["estado"] == "pendiente_plan"))
    col_m4.metric("📊 Total general", len(rows))

    # ── Calendario ───────────────────────────────────────────
    st.markdown(
        f"### 📅 {MONTH_NAMES_ES[month]} {year}"
        f"{'  —  ' + tipo_filtro if tipo_filtro != 'TODOS' else '  —  Todos los tipos'}"
    )
    cal_html = _render_calendar_html(month_tasks, year, month, dark)
    st.html(cal_html)

    st.divider()

    # ── Lista detallada: empresas del mes agrupadas ──────────
    st.markdown(f"### 🏢 Empresas con vencimiento en {MONTH_NAMES_ES[month]} {year}")

    if not month_tasks:
        st.info(
            "No hay empresas con vencimiento este mes. "
            "Sube un PDF de SUNAT en el panel de arriba para cargar el cronograma."
        )
    else:
        # Agrupar por empresa
        empresas_en_mes: dict[int, list] = {}
        for t in month_tasks:
            emp_id = t.get("empresa_id")
            if emp_id:
                empresas_en_mes.setdefault(emp_id, []).append(t)

        for emp_id, tareas in sorted(empresas_en_mes.items()):
            empresa = _get_empresa_by_id(emp_id)
            nombre_empresa = empresa["razon_social"] if empresa else f"Empresa ID {emp_id}"
            ruc = str(empresa.get("ruc", "")) if empresa else ""
            digito = ruc[-1] if ruc else "?"
            color = _get_empresa_color(emp_id)
            text_color = _get_contrast_text_color(color)

            # Badge de color con el nombre
            badge_html = (
                f'<span style="background:{color};color:{text_color};'
                f'border-radius:8px;padding:3px 10px;font-size:13px;font-weight:600;">'
                f'{nombre_empresa}</span>'
                f'&nbsp;<span style="color:#888;font-size:12px;">RUC termina en <b>{digito}</b></span>'
            )

            with st.container(border=True):
                col_e1, col_e2 = st.columns([6, 2])
                with col_e1:
                    st.markdown(badge_html, unsafe_allow_html=True)
                    for t in tareas:
                        fecha_txt = (
                            t["fecha_objetivo"].strftime("%d/%m/%Y")
                            if hasattr(t["fecha_objetivo"], "strftime")
                            else str(t["fecha_objetivo"])
                        )
                        tipo_badge = f"`{t.get('tipo_tarea','')}`"
                        st.markdown(f"  → {tipo_badge} Vence el **{fecha_txt}**")
                with col_e2:
                    if st.button(
                        f"📋 Ver todas las tareas",
                        key=f"btn_emp_{emp_id}",
                        use_container_width=True
                    ):
                        st.session_state.selected_empresa_id = emp_id
                        st.rerun()

    # ── Vista de todas las tareas de una empresa ─────────────
    if st.session_state.selected_empresa_id:
        empresa = _get_empresa_by_id(st.session_state.selected_empresa_id)
        if empresa:
            st.divider()
            ruc = str(empresa.get("ruc", ""))
            digito = ruc[-1] if ruc else "?"
            color = _get_empresa_color(empresa["id"])
            text_color = _get_contrast_text_color(color)

            st.markdown(
                f'<div style="background:{color};color:{text_color};border-radius:12px;'
                f'padding:14px 20px;margin-bottom:12px;">'
                f'<div style="font-size:20px;font-weight:700;">{empresa["razon_social"]}</div>'
                f'<div style="font-size:13px;opacity:0.85;">RUC: {ruc} &nbsp;|&nbsp; Último dígito: {digito}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            tareas_empresa = _get_tareas_por_empresa(empresa["id"])
            if not tareas_empresa:
                st.info("No hay tareas registradas para esta empresa.")
            else:
                df_tareas = pd.DataFrame(tareas_empresa)
                df_tareas = df_tareas.rename(columns={
                    "tarea_planeada": "Empresa",
                    "fecha_objetivo": "Fecha vencimiento",
                    "tipo_tarea": "Tipo",
                    "prioridad": "Prioridad",
                    "estado": "Estado",
                    "notas": "Notas",
                    "mes_vencimiento": "Mes"
                })
                df_tareas["Fecha vencimiento"] = pd.to_datetime(
                    df_tareas["Fecha vencimiento"]
                ).dt.strftime("%d/%m/%Y")
                df_tareas["Mes"] = df_tareas["Mes"].apply(lambda x: MONTH_NAMES_ES[int(x)])
                st.dataframe(
                    df_tareas[["Tipo", "Mes", "Fecha vencimiento", "Estado", "Notas"]],
                    use_container_width=True,
                    hide_index=True
                )

            if st.button("✖ Cerrar vista de empresa"):
                st.session_state.selected_empresa_id = None
                st.rerun()