import streamlit as st
from config.db import get_connection
from datetime import date
import calendar
import pdfplumber
import io
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ================================================================
#  CONSTANTES
# ================================================================

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

FERIADOS_PE = [
    date(2025, 1, 1),   # Año Nuevo
    date(2025, 4, 9),   # Miércoles de Ceniza
    date(2025, 4, 18),  # Viernes Santo
    date(2025, 5, 1),   # Día del Trabajo
    date(2025, 6, 29),  # San Pedro y San Pablo
    date(2025, 7, 28),  # Fiestas Patrias
    date(2025, 7, 29),  # Fiestas Patrias
    date(2025, 8, 30),  # Santa Rosa
    date(2025, 10, 8),  # Combate de Angamos
    date(2025, 11, 1),  # Día de Difuntos
    date(2025, 12, 9),  # Batalla de Ayacucho
    date(2025, 12, 25), # Navidad
    date(2026, 1, 1),   # Año Nuevo
    date(2026, 2, 25),  # Miércoles de Ceniza
    date(2026, 4, 3),   # Viernes Santo
    date(2026, 5, 1),   # Día del Trabajo
    date(2026, 6, 29),  # San Pedro y San Pablo
    date(2026, 7, 28),  # Fiestas Patrias
    date(2026, 7, 29),  # Fiestas Patrias
    date(2026, 8, 30),  # Santa Rosa
    date(2026, 10, 8),  # Combate de Angamos
    date(2026, 11, 1),  # Día de Difuntos
    date(2026, 12, 9),  # Batalla de Ayacucho
    date(2026, 12, 25), # Navidad
]

MESES_ABREV = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4,
    "may": 5, "jun": 6, "jul": 7, "ago": 8,
    "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

COL_GRUPOS = {
    1: 0,
    2: 1,
    3: "2y3",
    4: "4y5",
    5: "6y7",
    6: "8y9",
    7: "bc",
}


# ================================================================
#  PARSER PDF SUNAT
# ================================================================

def _parsear_fecha_celda(celda: str, anio_base: int):
    if not celda:
        return None
    partes = [p.strip().lower() for p in celda.replace("\n", " ").split()]
    try:
        dia  = int(partes[0])
        mes  = MESES_ABREV.get(partes[1][:3])
        anio = int(partes[2]) if len(partes) >= 3 else anio_base
        if mes:
            return date(anio, mes, dia)
    except Exception:
        pass
    return None


def _parsear_periodo(texto: str, anio_forzado: int):
    if not texto:
        return None, None

    texto = texto.strip().lower().rstrip("*").strip()

    if "-" in texto:
        partes = texto.split("-")
        mes = MESES_ABREV.get(partes[0][:3])
        try:
            anio_raw = int(partes[1])
            anio = anio_raw if anio_raw > 100 else 2000 + anio_raw
        except (ValueError, IndexError):
            return None, None
        return (anio, mes) if mes else (None, None)

    mes = MESES_ABREV.get(texto[:3])
    if mes:
        return anio_forzado, mes

    return None, None


def _leer_cronograma_pdf(pdf_bytes: bytes, anio_forzado: int) -> dict:
    resultado = {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for tabla in tables:
                for fila in tabla:
                    if not fila or not fila[0]:
                        continue

                    anio_per, mes_per = _parsear_periodo(fila[0], anio_forzado)
                    if not anio_per or not mes_per:
                        continue

                    anio_venc_base = anio_per if mes_per < 12 else anio_per + 1

                    fila_fechas = {}
                    for col_idx, grupo in COL_GRUPOS.items():
                        if col_idx < len(fila) and fila[col_idx]:
                            fecha = _parsear_fecha_celda(fila[col_idx], anio_venc_base)
                            if fecha:
                                fila_fechas[grupo] = fecha

                    if fila_fechas:
                        resultado[(anio_per, mes_per)] = fila_fechas

    return resultado


# ================================================================
#  HELPERS RUC -> GRUPO
# ================================================================

def _get_digito_grupo(ruc: str):
    if not ruc:
        return None
    d = int(ruc[-1])
    if d == 0:       return 0
    if d == 1:       return 1
    if d in (2, 3):  return "2y3"
    if d in (4, 5):  return "4y5"
    if d in (6, 7):  return "6y7"
    if d in (8, 9):  return "8y9"
    return None


def _get_fecha_vencimiento_from_cron(ruc: str, cronograma: dict, anio: int, mes: int):
    grupo  = _get_digito_grupo(ruc)
    fechas = cronograma.get((anio, mes), {})
    return fechas.get(grupo)


def _es_dia_habil(fecha: date) -> bool:
    if fecha.weekday() in (5, 6):
        return False
    if fecha in FERIADOS_PE:
        return False
    return True


def _calcular_fecha_inicio(fecha_meta: date, dias_antes: int = 3) -> date:
    from datetime import timedelta

    dias_restados = 0
    fecha_actual = fecha_meta

    while dias_restados < dias_antes:
        fecha_actual -= timedelta(days=1)
        if _es_dia_habil(fecha_actual):
            dias_restados += 1

    while not _es_dia_habil(fecha_actual):
        fecha_actual -= timedelta(days=1)

    return fecha_actual


def _exportar_cronograma_imagen(registros: list, mes: int, anio: int) -> io.BytesIO:
    """
    Exporta el calendario tal cual se visualiza en la página utilizando la lógica de cuadrícula oscura.
    """
    reg_por_dia = {}
    for r in registros:
        d = r["fecha_vencimiento"].day
        reg_por_dia.setdefault(d, []).append(r)

    primer_dia_semana, dias_en_mes = calendar.monthrange(anio, mes)
    celdas = [None] * primer_dia_semana + list(range(1, dias_en_mes + 1))
    while len(celdas) % 7 != 0:
        celdas.append(None)
    semanas = [celdas[i:i+7] for i in range(0, len(celdas), 7)]
    n_semanas = len(semanas)

    FIG_W  = 20
    CELL_H = 2.2
    HEAD_H = 1.2   
    FIG_H  = HEAD_H + n_semanas * CELL_H

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.set_xlim(0, 7)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    ax.text(3.5, FIG_H - 0.3,
            f"{MESES_ES[mes]} {anio}",
            ha="center", va="top",
            fontsize=22, fontweight="bold",
            color="#f6c27d", fontfamily="monospace")

    DIAS_COLS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    for i, nombre in enumerate(DIAS_COLS):
        color = "#F09595" if i == 6 else "#f6c27d" if i == 5 else "#aaaacc"
        ax.text(i + 0.5, FIG_H - 0.75, nombre,
                ha="center", va="center",
                fontsize=11, fontweight="bold",
                color=color, fontfamily="monospace")

    for sem_idx, semana in enumerate(semanas):
        y_top = FIG_H - HEAD_H - sem_idx * CELL_H

        for col_idx, dia in enumerate(semana):
            x = col_idx
            y = y_top - CELL_H

            es_fin = col_idx >= 5
            bg = "#16213e" if not es_fin else "#1e1a2e"
            rect = FancyBboxPatch((x + 0.03, y + 0.03),
                                  0.94, CELL_H - 0.06,
                                  boxstyle="round,pad=0.02",
                                  facecolor=bg,
                                  edgecolor="#2a2a4a", linewidth=0.8)
            ax.add_patch(rect)

            if dia is None:
                continue

            hoy = date.today()
            es_hoy = (dia == hoy.day and mes == hoy.month and anio == hoy.year)

            num_color = "#f6c27d" if es_hoy else ("#F09595" if es_fin else "#ddddee")
            if es_hoy:
                circ = plt.Circle((x + 0.22, y + CELL_H - 0.28), 0.17,
                                  color="#f6c27d", zorder=3)
                ax.add_patch(circ)
                num_color = "#1a1a2e"

            ax.text(x + 0.22, y + CELL_H - 0.28, str(dia),
                    ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    color=num_color, fontfamily="monospace", zorder=4)

            regs = reg_por_dia.get(dia, [])
            max_chips = 3
            for chip_i, r in enumerate(regs[:max_chips]):
                chip_y = y + CELL_H - 0.62 - chip_i * 0.48
                c_bg  = "#1a3a2e" if r["asignado"] else "#2e2a1a"
                c_bar = "#5DCAA5" if r["asignado"] else "#f6c27d"

                ax.add_patch(FancyBboxPatch(
                    (x + 0.08, chip_y - 0.17), 0.03, 0.34,
                    boxstyle="square,pad=0",
                    facecolor=c_bar, edgecolor="none"))

                ax.add_patch(FancyBboxPatch(
                    (x + 0.11, chip_y - 0.17), 0.82, 0.34,
                    boxstyle="round,pad=0.01",
                    facecolor=c_bg, edgecolor="none"))

                empresa = r["empresa"][:12]
                ax.text(x + 0.52, chip_y + 0.04,
                        empresa,
                        ha="center", va="center",
                        fontsize=6.5, color="#ddddee",
                        fontfamily="monospace",
                        clip_on=True)

                tarea = r["tarea"][:14]
                ax.text(x + 0.52, chip_y - 0.11,
                        tarea,
                        ha="center", va="center",
                        fontsize=5.5, color="#888899",
                        fontfamily="monospace",
                        clip_on=True)

            if len(regs) > max_chips:
                ax.text(x + 0.52, y + 0.12,
                        f"+{len(regs)-max_chips} más",
                        ha="center", va="center",
                        fontsize=6, color="#888899",
                        fontfamily="monospace")

    leyenda_y = 0.35
    for lx, color, label in [
        (0.3, "#5DCAA5", "Asignado"),
        (1.5, "#f6c27d", "Pendiente"),
    ]:
        ax.add_patch(mpatches.Rectangle((lx, leyenda_y - 0.12), 0.18, 0.22, color=color))
        ax.text(lx + 0.25, leyenda_y, label,
                va="center", fontsize=8,
                color="#aaaacc", fontfamily="monospace")

    plt.tight_layout(pad=0.3)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150,
                facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ================================================================
#  REPOSITORIO
# ================================================================

def _get_empresas_activas():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, razon_social, alias, ruc
        FROM empresas
        WHERE estado_contrato = 'Activo'
        ORDER BY razon_social
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_usuarios_activos():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, nom_res, alias
        FROM usuarios
        WHERE estado = 'activo' AND rol = 'trabajador'
        ORDER BY nom_res
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_tareas_pdt():
    """Solo tareas PDT 621."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT t.id, t.nombre_tarea, p.nombre_proyecto
        FROM tareas t
        JOIN proyectos p ON t.proyecto_id = p.id
        WHERE t.nombre_tarea ILIKE '%PDT%621%'
        ORDER BY p.nombre_proyecto, t.nombre_tarea
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_tareas_le():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT t.id, t.nombre_tarea, p.nombre_proyecto
        FROM tareas t
        JOIN proyectos p ON t.proyecto_id = p.id
        WHERE t.nombre_tarea ILIKE '%LE%V-C%VALIDACION%'
           OR (t.nombre_tarea ILIKE '%LE%V-C%'
               AND t.nombre_tarea NOT ILIKE '%VALIDACION%')
        ORDER BY
            CASE WHEN t.nombre_tarea ILIKE '%VALIDACION%' THEN 1 ELSE 2 END,
            t.nombre_tarea
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_cronograma_mes(anio: int, mes: int):
    """
    Devuelve la combinación unificada de tareas del cronograma del PDF 
    y de las asignaciones manuales/Excel para el mes y año seleccionados.
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        /* 1. Traer los datos del cronograma cargado por PDF */
        SELECT
            c.id::text AS id, 
            c.periodo_mes, 
            c.periodo_anio,
            c.fecha_vencimiento, 
            c.asignado,
            e.alias AS empresa, 
            e.ruc, 
            e.id AS empresa_id,
            t.nombre_tarea AS tarea, 
            t.id AS tarea_id,
            'pdf' AS tipo_origen
        FROM cronograma_pdt c
        JOIN empresas e ON c.empresa_id = e.id
        JOIN tareas   t ON c.tarea_id   = t.id
        WHERE EXTRACT(YEAR  FROM c.fecha_vencimiento) = %s
          AND EXTRACT(MONTH FROM c.fecha_vencimiento) = %s

        UNION ALL

        /* 2. Combinar y estructurar las asignaciones manuales/Excel */
        SELECT DISTINCT ON (a.id)
            'manual_' || a.id::text AS id,
            EXTRACT(MONTH FROM a.fecha_meta)::int AS periodo_mes,
            EXTRACT(YEAR  FROM a.fecha_meta)::int AS periodo_anio,
            a.fecha_meta AS fecha_vencimiento,
            TRUE AS asignado,
            e.alias AS empresa,
            e.ruc,
            e.id AS empresa_id,
            t.nombre_tarea AS tarea,
            t.id AS tarea_id,
            'manual' AS tipo_origen
        FROM asignaciones a
        JOIN empresas e ON a.empresa_id = e.id
        JOIN tareas   t ON a.tarea_id   = t.id
        WHERE NOT EXISTS (
            SELECT 1 FROM cronograma_pdt cp 
            WHERE cp.empresa_id = a.empresa_id 
              AND cp.tarea_id = a.tarea_id 
              AND cp.fecha_vencimiento = a.fecha_meta
        )
        AND EXTRACT(YEAR  FROM a.fecha_meta) = %s
        AND EXTRACT(MONTH FROM a.fecha_meta) = %s

        ORDER BY fecha_vencimiento ASC, empresa ASC
    """, (anio, mes, anio, mes))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _ya_existe_cronograma(empresa_id, tarea_id, anio, mes) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id FROM cronograma_pdt
        WHERE empresa_id=%s AND tarea_id=%s AND periodo_anio=%s AND periodo_mes=%s
        LIMIT 1
    """, (empresa_id, tarea_id, anio, mes))
    existe = cur.fetchone() is not None
    cur.close(); conn.close()
    return existe


def _insertar_cronograma_bulk(filas: list):
    conn = get_connection()
    cur  = conn.cursor()
    ok = err = 0
    errores = []
    try:
        for f in filas:
            try:
                cur.execute("""
                    INSERT INTO cronograma_pdt
                        (tarea_id, empresa_id, periodo_mes, periodo_anio, fecha_vencimiento)
                    VALUES (%s, %s, %s, %s, %s)
                """, (f["tarea_id"], f["empresa_id"],
                      f["periodo_mes"], f["periodo_anio"],
                      f["fecha_vencimiento"]))
                ok += 1
            except Exception as ex:
                errores.append(str(ex))
                err += 1
        conn.commit()
    except Exception as ex:
        conn.rollback()
        errores.append(str(ex))
    finally:
        cur.close(); conn.close()
    return ok, err, errores


def _asignar_desde_cronograma(cronograma_id, usuario_ids, empresa_id, tarea_id, fecha_vencimiento, peso=1):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT get_next_asignacion_id() AS nuevo_id")
        nuevo_id = cur.fetchone()["nuevo_id"]

        for uid in usuario_ids:
            cur.execute("""
                INSERT INTO asignaciones
                    (id, usuario_id, empresa_id, tarea_id, fecha_meta, estado, peso)
                OVERRIDING SYSTEM VALUE
                VALUES (%s, %s, %s, %s, %s, 'pendiente', %s)
            """, (nuevo_id, uid, empresa_id, tarea_id, fecha_vencimiento, peso))

        cur.execute("UPDATE cronograma_pdt SET asignado=TRUE WHERE id=%s", (cronograma_id,))
        conn.commit()
        return True, nuevo_id
    except Exception as ex:
        conn.rollback()
        return False, str(ex)
    finally:
        cur.close(); conn.close()


# ================================================================
#  HELPERS UI
# ================================================================

def _badge_asignado(asignado: bool) -> str:
    if asignado:
        return '<span style="background:rgba(93,202,165,0.15);color:#5DCAA5;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;">ASIGNADO</span>'
    return '<span style="background:rgba(246,194,125,0.15);color:#f6c27d;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;">PENDIENTE</span>'


def _selector_anio_y_meses(key_prefix: str, hoy: date):
    c1, c2 = st.columns([1, 2])
    with c1:
        anio = st.selectbox(
            "Año del cronograma *",
            options=list(range(2024, 2030)),
            index=list(range(2024, 2030)).index(hoy.year),
            key=f"{key_prefix}_anio"
        )
    with c2:
        meses = st.multiselect(
            "Períodos a importar *",
            options=list(range(1, 13)),
            default=[hoy.month],
            format_func=lambda m: MESES_ES[m],
            key=f"{key_prefix}_meses"
        )
    return anio, meses


def _procesar_preview(cronograma_pdf: dict, tarea_id: int,
                      anio: int, meses: list, empresas: list, dias_antes: int = 3) -> list:
    filas = []
    for mes in sorted(meses):
        for emp in empresas:
            fecha_sunat = _get_fecha_vencimiento_from_cron(emp["ruc"], cronograma_pdf, anio, mes)
            if not fecha_sunat:
                continue
            ya_existe = _ya_existe_cronograma(emp["id"], tarea_id, anio, mes)
            fecha_ajustada = _calcular_fecha_inicio(fecha_sunat, dias_antes)
            filas.append({
                "Período":           f"{MESES_ES[mes]} {anio}",
                "Empresa":           emp["alias"],
                "RUC":               emp["ruc"],
                "Últ. dígito":       emp["ruc"][-1] if emp["ruc"] else "?",
                "Tarea":             "",
                "F. SUNAT (orig.)":  fecha_sunat.strftime("%d/%m/%Y"),
                "F. Programada (BD)": fecha_ajustada.strftime("%d/%m/%Y"),
                "Estado":            "Ya existe" if ya_existe else "Nuevo",
                "_empresa_id":       emp["id"],
                "_tarea_id":         tarea_id,
                "_mes":              mes,
                "_anio":             anio,
                "_fecha_sunat":      fecha_sunat,
                "_fecha_bd":         fecha_ajustada,   
                "_existe":           ya_existe,
                "_dias_antes":       dias_antes,
            })
    return filas


def _render_preview_y_confirmar(filas: list, session_key: str):
    nuevos = [f for f in filas if not f["_existe"]]
    ya_hay = [f for f in filas if f["_existe"]]

    df = pd.DataFrame([{k: v for k, v in f.items() if not k.startswith("_")} for f in filas])
    st.markdown(f"**Vista previa — {len(filas)} registros:**")
    st.dataframe(df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    c1.markdown(
        f"<span style='color:#5DCAA5;font-size:12px;'>{len(nuevos)} nuevos a insertar</span>",
        unsafe_allow_html=True
    )
    c2.markdown(
        f"<span style='color:#f6c27d;font-size:12px;'>{len(ya_hay)} ya existentes (se omitirán)</span>",
        unsafe_allow_html=True
    )

    if nuevos:
        if st.button("Confirmar importación", type="primary",
                     use_container_width=True, key=f"btn_confirmar_{session_key}"):
            filas_bd = [{
                "tarea_id":          f["_tarea_id"],
                "empresa_id":        f["_empresa_id"],
                "periodo_mes":       f["_mes"],
                "periodo_anio":      f["_anio"],
                "fecha_vencimiento": f["_fecha_bd"],   
            } for f in nuevos]

            ok_c, err_c, errs = _insertar_cronograma_bulk(filas_bd)
            if ok_c:
                st.session_state.cron_msg                  = ("ok", f"{ok_c} registros importados correctamente.")
                st.session_state[f"preview_{session_key}"] = None
            if err_c:
                st.session_state.cron_msg = ("error", f"{err_c} errores: {' | '.join(errs[:3])}")
            st.rerun()
    else:
        st.info("Todos los registros ya existen para los períodos seleccionados.")

    if st.button("Limpiar vista previa", key=f"btn_limpiar_{session_key}"):
        st.session_state[f"preview_{session_key}"] = None
        st.rerun()


# ================================================================
#  VISTA PRINCIPAL
# ================================================================

def admin_cronograma():

    st.markdown("""
    <div style="margin-bottom:24px;">
        <h2 style="color:#f6c27d;font-size:22px;font-weight:800;margin:0;">Cronograma de Tareas</h2>
        <p style="color:rgba(255,255,255,0.5);font-size:13px;margin-top:4px;">
            Importa el cronograma SUNAT desde PDF · Vista por fecha programada · Asigna trabajadores
        </p>
    </div>
    """, unsafe_allow_html=True)

    for key, val in {
        "cron_msg":       None,
        "cron_asig_id":   None,
        "cron_asig_open": False,
        "preview_pdt":    None,
        "preview_le":     None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = val

    if st.session_state.cron_msg:
        tipo, texto = st.session_state.cron_msg
        (st.success if tipo == "ok" else st.error)(texto)
        st.session_state.cron_msg = None

    hoy = date.today()

    tab_cal, tab_pdt, tab_le = st.tabs([
        "📅 Calendario",
        "📄 Importar PDT 621",
        "📚 Importar LE",
    ])

    # ================================================================
    #  TAB PDT 621
    # ================================================================
    with tab_pdt:
        st.markdown("""
        <div style="background:rgba(93,202,165,0.06);border:1px solid rgba(93,202,165,0.2);
                    border-radius:16px;padding:20px 24px;margin-bottom:20px;">
            <h4 style="color:#5DCAA5;margin:0 0 6px;">Importar Cronograma PDT 621</h4>
            <p style="color:rgba(255,255,255,0.5);font-size:12px;margin:0;">
                Sube el PDF del cronograma SUNAT para PDT 621.
                Selecciona el año del cronograma y los períodos a importar.
            </p>
        </div>
        """, unsafe_allow_html=True)

        tareas_pdt = _get_tareas_pdt()
        if not tareas_pdt:
            st.warning("No se encontró la tarea PDT 621 en la base de datos.")
        else:
            st.markdown(
                "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(93,202,165,0.15);"
                "border-left:3px solid #5DCAA5;border-radius:8px;padding:10px 14px;margin-bottom:16px;"
                "font-size:12px;color:rgba(255,255,255,0.6);'>"
                "Tareas que se importarán con este PDF: "
                + " &nbsp;·&nbsp; ".join(
                    f"<span style='color:#5DCAA5;font-weight:700;'>{t['nombre_tarea']}</span>"
                    for t in tareas_pdt
                )
                + "</div>",
                unsafe_allow_html=True
            )

            st.markdown("""
            <div style="background:rgba(246,194,125,0.06);border:1px solid rgba(246,194,125,0.2);
                        border-radius:12px;padding:14px 18px;margin-bottom:16px;">
                <span style="color:#f6c27d;font-size:13px;font-weight:700;">
                    ⚙️ Configuración de fechas
                </span>
                <p style="color:rgba(255,255,255,0.45);font-size:11px;margin:4px 0 0;">
                    Las fechas se guardarán en BD con el ajuste indicado (días hábiles antes de la fecha SUNAT).
                </p>
            </div>
            """, unsafe_allow_html=True)

            dias_antes_pdt = st.number_input(
                "Días hábiles antes de la fecha SUNAT para programar la tarea *",
                min_value=1, max_value=10, value=3, key="pdt_dias_antes"
            )

            anio_pdt, meses_pdt = _selector_anio_y_meses("pdt", hoy)

            pdf_pdt = st.file_uploader(
                "PDF del cronograma PDT 621",
                type=["pdf"],
                key="pdf_uploader_pdt"
            )

            if pdf_pdt and meses_pdt:
                if st.button("Leer PDF y generar vista previa",
                             use_container_width=True, key="btn_leer_pdt"):
                    try:
                        cronograma_pdf = _leer_cronograma_pdf(pdf_pdt.read(), anio_pdt)
                        empresas       = _get_empresas_activas()

                        filas_total = []
                        for tarea in tareas_pdt:
                            filas_tarea = _procesar_preview(
                                cronograma_pdf, tarea["id"], anio_pdt, meses_pdt, empresas, dias_antes_pdt
                            )
                            for f in filas_tarea:
                                f["Tarea"] = tarea["nombre_tarea"]
                            filas_total.extend(filas_tarea)

                        st.session_state.preview_pdt = filas_total

                        if not filas_total:
                            st.warning("No se encontraron coincidencias entre el PDF y las empresas activas.")
                        else:
                            for tarea in tareas_pdt:
                                n_new = sum(1 for f in filas_total if f["_tarea_id"] == tarea["id"] and not f["_existe"])
                                n_dup = sum(1 for f in filas_total if f["_tarea_id"] == tarea["id"] and f["_existe"])
                                st.caption(
                                    f"→ {tarea['nombre_tarea']}: "
                                    f"{n_new} nuevos  |  {n_dup} ya existentes"
                                )
                    except Exception as ex:
                        st.error(f"Error al leer el PDF: {ex}")

            if st.session_state.preview_pdt:
                _render_preview_y_confirmar(st.session_state.preview_pdt, "pdt")

    # ================================================================
    #  TAB LE
    # ================================================================
    with tab_le:
        st.markdown("""
        <div style="background:rgba(133,183,235,0.06);border:1px solid rgba(133,183,235,0.2);
                    border-radius:16px;padding:20px 24px;margin-bottom:20px;">
            <h4 style="color:#85B7EB;margin:0 0 6px;">Importar Cronograma LE — Libro Electrónico</h4>
            <p style="color:rgba(255,255,255,0.5);font-size:12px;margin:0;">
                <b>LE V-C VALIDACION</b> y <b>LE V-C</b> comparten el mismo cronograma PDF.
                Con un solo upload se importan registros para <b>ambas tareas simultáneamente</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)

        tareas_le = _get_tareas_le()
        if not tareas_le:
            st.warning("No se encontraron tareas LE en la base de datos.")
        else:
            st.markdown(
                "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(133,183,235,0.15);"
                "border-left:3px solid #85B7EB;border-radius:8px;padding:10px 14px;margin-bottom:16px;"
                "font-size:12px;color:rgba(255,255,255,0.6);'>"
                "Tareas que se importarán con este PDF: "
                + " &nbsp;·&nbsp; ".join(
                    f"<span style='color:#85B7EB;font-weight:700;'>{t['nombre_tarea']}</span>"
                    for t in tareas_le
                )
                + "</div>",
                unsafe_allow_html=True
            )

            st.markdown("""
            <div style="background:rgba(246,194,125,0.06);border:1px solid rgba(246,194,125,0.2);
                        border-radius:12px;padding:14px 18px;margin-bottom:16px;">
                <span style="color:#f6c27d;font-size:13px;font-weight:700;">
                    ⚙️ Configuración de fechas
                </span>
                <p style="color:rgba(255,255,255,0.45);font-size:11px;margin:4px 0 0;">
                    Las fechas se guardarán en BD con el ajuste indicado (días hábiles antes de la fecha SUNAT).
                </p>
            </div>
            """, unsafe_allow_html=True)

            dias_antes_le = st.number_input(
                "Días hábiles antes de la fecha SUNAT para programar la tarea *",
                min_value=1, max_value=10, value=3, key="le_dias_antes"
            )

            anio_le, meses_le = _selector_anio_y_meses("le", hoy)

            pdf_le = st.file_uploader(
                "PDF del cronograma LE (válido para LE V-C VALIDACION y LE V-C)",
                type=["pdf"],
                key="pdf_uploader_le"
            )

            if pdf_le and meses_le:
                if st.button("Leer PDF y generar vista previa",
                             use_container_width=True, key="btn_leer_le"):
                    try:
                        cronograma_pdf = _leer_cronograma_pdf(pdf_le.read(), anio_le)
                        empresas       = _get_empresas_activas()

                        filas_total = []
                        for tarea in tareas_le:
                            filas_tarea = _procesar_preview(
                                cronograma_pdf, tarea["id"], anio_le, meses_le, empresas, dias_antes_le
                            )
                            for f in filas_tarea:
                                f["Tarea"] = tarea["nombre_tarea"]
                            filas_total.extend(filas_tarea)

                        st.session_state.preview_le = filas_total

                        if not filas_total:
                            st.warning("No se encontraron coincidencias entre el PDF y las empresas activas.")
                        else:
                            for tarea in tareas_le:
                                n_new = sum(1 for f in filas_total if f["_tarea_id"] == tarea["id"] and not f["_existe"])
                                n_dup = sum(1 for f in filas_total if f["_tarea_id"] == tarea["id"] and f["_existe"])
                                st.caption(
                                    f"→ {tarea['nombre_tarea']}: "
                                    f"{n_new} nuevos  |  {n_dup} ya existentes"
                                )

                    except Exception as ex:
                        st.error(f"Error al leer el PDF: {ex}")

            if st.session_state.preview_le:
                _render_preview_y_confirmar(st.session_state.preview_le, "le")

    # ================================================================
    #  TAB CALENDARIO
    # ================================================================
    with tab_cal:

        col_mes, col_anio = st.columns([2, 1])
        with col_mes:
            mes_sel = st.selectbox(
                "Mes",
                options=list(range(1, 13)),
                format_func=lambda m: MESES_ES[m],
                index=hoy.month - 1,
                key="cron_mes"
            )
        with col_anio:
            anio_sel = st.selectbox(
                "Año",
                options=list(range(2024, 2030)),
                index=list(range(2024, 2030)).index(hoy.year),
                key="cron_anio"
            )

        st.markdown("""
        <div style="background:rgba(133,183,235,0.06);border:1px solid rgba(133,183,235,0.15);
                    border-radius:10px;padding:10px 14px;margin:8px 0 16px;">
            <span style="color:#85B7EB;font-size:12px;">
                <b>📌 Fechas programadas:</b> Las fechas mostradas son las ya ajustadas (guardadas en BD),
                calculadas restando los días hábiles configurados al momento de importar el PDF.
            </span>
        </div>
        """, unsafe_allow_html=True)

        registros = _get_cronograma_mes(anio_sel, mes_sel)

        reg_por_dia = {}
        for r in registros:
            fecha_mostrar = r["fecha_vencimiento"]
            if fecha_mostrar.year == anio_sel and fecha_mostrar.month == mes_sel:
                d = fecha_mostrar.day
                reg_por_dia.setdefault(d, []).append(r)

        total_reg  = len(registros)
        asignados  = sum(1 for r in registros if r["asignado"])
        pendientes = total_reg - asignados

        m1, m2, m3 = st.columns(3)
        for col, label, val, color in [
            (m1, "Total empresas", total_reg,  "white"),
            (m2, "Asignados",      asignados,  "#5DCAA5"),
            (m3, "Sin asignar",    pendientes, "#f6c27d"),
        ]:
            col.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
                        border-radius:12px;padding:12px 16px;margin-bottom:16px;">
                <div style="color:rgba(255,255,255,0.4);font-size:10px;letter-spacing:1px;
                            text-transform:uppercase;margin-bottom:4px;">{label}</div>
                <div style="color:{color};font-size:22px;font-weight:800;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin:8px 0 16px;">
            <span style="color:#f6c27d;font-size:18px;font-weight:800;">
                {MESES_ES[mes_sel]} {anio_sel}
            </span>
            <span style="color:rgba(255,255,255,0.3);font-size:12px;margin-left:8px;">
                — fechas programadas (ajustadas)
            </span>
        </div>
        """, unsafe_allow_html=True)

        cols_h = st.columns(7)
        for i, dia_nombre in enumerate(DIAS_ES):
            color = "#F09595" if i == 6 else "#f6c27d" if i == 5 else "rgba(255,255,255,0.4)"
            cols_h[i].markdown(
                f"<div style='text-align:center;color:{color};font-size:11px;"
                f"font-weight:700;letter-spacing:1px;padding:8px 0;'>{dia_nombre}</div>",
                unsafe_allow_html=True
            )

        primer_dia_semana, dias_en_mes = calendar.monthrange(anio_sel, mes_sel)
        celdas = [""] * primer_dia_semana + list(range(1, dias_en_mes + 1))
        while len(celdas) % 7 != 0:
            celdas.append("")
        semanas = [celdas[i:i+7] for i in range(0, len(celdas), 7)]

        for week in semanas:
            cols = st.columns(7)
            for col_idx, dia in enumerate(week):
                with cols[col_idx]:
                    if dia == "":
                        st.markdown("<div style='min-height:100px;'></div>", unsafe_allow_html=True)
                        continue

                    es_hoy   = (dia == hoy.day and mes_sel == hoy.month and anio_sel == hoy.year)
                    es_fin   = col_idx >= 5
                    regs_dia = reg_por_dia.get(dia, [])

                    num_color = "#f6c27d" if es_hoy else ("#F09595" if es_fin else "rgba(255,255,255,0.7)")
                    num_bg    = "rgba(246,194,125,0.15)" if es_hoy else "transparent"
                    borde     = "1px solid rgba(246,194,125,0.4)" if es_hoy else "1px solid rgba(255,255,255,0.06)"

                    chips_html = ""
                    for r in regs_dia[:3]:
                        c       = "#5DCAA5" if r["asignado"] else "#f6c27d"
                        empresa = r["empresa"][:10]
                        tarea   = r["tarea"][:8]
                        chips_html += (
                            f'<div style="background:rgba(255,255,255,0.04);border-left:3px solid {c};'
                            f'padding:2px 5px;border-radius:0 4px 4px 0;margin-bottom:2px;">'
                            f'<div style="font-size:9px;color:rgba(255,255,255,0.85);white-space:nowrap;'
                            f'overflow:hidden;text-overflow:ellipsis;font-weight:600;">{empresa}</div>'
                            f'<div style="font-size:8px;color:rgba(255,255,255,0.4);white-space:nowrap;'
                            f'overflow:hidden;text-overflow:ellipsis;">{tarea}</div>'
                            f'</div>'
                        )
                    if len(regs_dia) > 3:
                        chips_html += (
                            f'<div style="color:rgba(255,255,255,0.35);font-size:9px;'
                            f'padding-left:4px;">+{len(regs_dia)-3} más</div>'
                        )

                    hoy_badge = "<span style='color:#f6c27d;font-size:9px;'>HOY</span>" if es_hoy else ""
                    html_cell = (
                        f'<div style="background:rgba(255,255,255,0.02);border:{borde};'
                        f'border-radius:10px;padding:8px 6px;min-height:100px;margin-bottom:4px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                        f'<span style="background:{num_bg};color:{num_color};font-size:13px;font-weight:700;'
                        f'padding:1px 6px;border-radius:6px;">{dia}</span>{hoy_badge}</div>'
                        f'{chips_html}</div>'
                    )
                    st.markdown(html_cell, unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        if registros:
            col_titulo, col_btn = st.columns([3, 1])
            with col_titulo:
                st.markdown(f"""
                <div style="margin-bottom:12px;">
                    <span style="color:rgba(255,255,255,0.6);font-size:14px;font-weight:600;">
                        Cronograma {MESES_ES[mes_sel]} {anio_sel} — fechas programadas
                    </span>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                img_buffer = _exportar_cronograma_imagen(registros, mes_sel, anio_sel)
                st.download_button(
                    label="📥 Descargar Imagen",
                    data=img_buffer,
                    file_name=f"cronograma_{MESES_ES[mes_sel]}_{anio_sel}.png",
                    mime="image/png",
                    use_container_width=True
                )

            cols_h2 = st.columns([0.4, 0.9, 1.1, 0.8, 1.1, 1.1, 0.8, 1])
            for col, h in zip(cols_h2, ["DIA", "PERÍODO", "EMPRESA", "RUC", "TAREA", "F. PROGRAMADA", "ESTADO", "ACCIÓN"]):
                col.markdown(
                    f"<span style='color:rgba(255,255,255,0.4);font-size:10px;"
                    f"font-weight:700;letter-spacing:1px;'>{h}</span>",
                    unsafe_allow_html=True
                )
            st.divider()

            for r in registros:
                fecha_programada = r['fecha_vencimiento']  

                with st.container(border=True):
                    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([0.4, 0.9, 1.1, 0.8, 1.1, 1.1, 0.8, 1])

                    c1.markdown(f"<span style='color:#f6c27d;font-weight:700;'>{fecha_programada.day}</span>", unsafe_allow_html=True)
                    c2.markdown(f"<span style='color:rgba(255,255,255,0.45);font-size:11px;'>{MESES_ES[r['periodo_mes']]} {r['periodo_anio']}</span>", unsafe_allow_html=True)
                    c3.markdown(f"<span style='color:white;font-size:12px;'>{r['empresa']}</span>", unsafe_allow_html=True)
                    c4.markdown(f"<span style='color:rgba(255,255,255,0.5);font-size:11px;'>{r['ruc']}</span>", unsafe_allow_html=True)
                    c5.markdown(f"<span style='color:rgba(255,255,255,0.7);font-size:12px;'>{r['tarea']}</span>", unsafe_allow_html=True)
                    c6.markdown(f"<span style='color:#85B7EB;font-size:12px;font-weight:600;'>{fecha_programada.strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)
                    c7.markdown(_badge_asignado(r["asignado"]), unsafe_allow_html=True)

                    with c8:
                        if isinstance(r["id"], str) and r["id"].startswith("manual"):
                            st.markdown("<span style='color:#5DCAA5;font-size:11px;'>manual</span>", unsafe_allow_html=True)
                        elif not r["asignado"]:
                            if st.button("Asignar", key=f"asig_{r['id']}", use_container_width=True):
                                st.session_state.cron_asig_id   = r["id"]
                                st.session_state.cron_asig_open = True
                                st.rerun()
                        else:
                            st.markdown("<span style='color:rgba(255,255,255,0.3);font-size:11px;'>listo</span>", unsafe_allow_html=True)

                if st.session_state.cron_asig_open and st.session_state.cron_asig_id == r["id"]:
                    st.markdown(f"""
                    <div style="background:rgba(133,183,235,0.06);border:1px solid rgba(133,183,235,0.2);
                                border-radius:16px;padding:20px 24px;margin:4px 0 12px;">
                        <h4 style="color:#85B7EB;margin:0 0 4px;">Asignar — {r['empresa']}</h4>
                        <p style="color:rgba(255,255,255,0.4);font-size:12px;margin:0;">
                            Período: {MESES_ES[r['periodo_mes']]} {r['periodo_anio']} ·
                            Tarea: {r['tarea']} ·
                            Fecha programada: {r['fecha_vencimiento'].strftime('%d/%m/%Y')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    usuarios = _get_usuarios_activos()
                    usr_map  = {f"{u['nom_res']} ({u['alias']})": u["id"] for u in usuarios}

                    col_u, col_p = st.columns(2)
                    with col_u:
                        usr_sel = st.multiselect(
                            "Trabajador(es) *", list(usr_map.keys()),
                            key=f"usr_sel_{r['id']}"
                        )
                    with col_p:
                        peso = st.number_input(
                            "Peso", min_value=1, max_value=10,
                            value=1, key=f"peso_sel_{r['id']}"
                        )

                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Confirmar", use_container_width=True,
                                     type="primary", key=f"confirm_asig_{r['id']}"):
                            if not usr_sel:
                                st.session_state.cron_msg = ("error", "Selecciona al menos un trabajador.")
                            else:
                                uid_list = [usr_map[n] for n in usr_sel]
                                ok, result = _asignar_desde_cronograma(
                                    cronograma_id=r["id"],
                                    usuario_ids=uid_list,
                                    empresa_id=r["empresa_id"],
                                    tarea_id=r["tarea_id"],
                                    fecha_vencimiento=r["fecha_vencimiento"],  
                                    peso=peso,
                                )
                                if ok:
                                    st.session_state.cron_msg       = ("ok", f"Asignación #{result} creada.")
                                    st.session_state.cron_asig_open = False
                                    st.session_state.cron_asig_id   = None
                                else:
                                    st.session_state.cron_msg = ("error", f"Error: {result}")
                            st.rerun()
                    with b2:
                        if st.button("Cancelar", use_container_width=True,
                                     key=f"cancel_asig_{r['id']}"):
                            st.session_state.cron_asig_open = False
                            st.session_state.cron_asig_id   = None
                            st.rerun()

        else:
            st.info(
                f"No hay vencimientos en {MESES_ES[mes_sel]} {anio_sel}. "
                f"Usa 'Importar PDT 621' o 'Importar LE' para cargar el cronograma."
            )