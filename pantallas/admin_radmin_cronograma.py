import streamlit as st
from config.db import get_connection
from datetime import date
import calendar
import pdfplumber
import io

# ================================================================
#  CONSTANTES
# ================================================================

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

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


def _parsear_periodo(texto: str):
    if not texto:
        return None, None
    partes = texto.strip().lower().split("-")
    if len(partes) != 2:
        return None, None
    mes  = MESES_ABREV.get(partes[0][:3])
    try:
        anio = int(partes[1])
    except ValueError:
        return None, None
    return anio, mes


def _leer_cronograma_pdf(pdf_bytes: bytes) -> dict:
    resultado = {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for tabla in tables:
                for fila in tabla:
                    if not fila or not fila[0]:
                        continue
                    periodo_txt = fila[0].strip()
                    anio_per, mes_per = _parsear_periodo(periodo_txt)
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
    if not ruc or len(ruc) < 1:
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


def _get_tareas():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT t.id, t.nombre_tarea, p.nombre_proyecto
        FROM tareas t
        JOIN proyectos p ON t.proyecto_id = p.id
        ORDER BY p.nombre_proyecto, t.nombre_tarea
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


# ================================================================
#  FIX: filtra por fecha_vencimiento, NO por periodo_mes/periodo_anio
# ================================================================
def _get_cronograma_mes(anio: int, mes: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
            c.id, c.periodo_mes, c.periodo_anio,
            c.fecha_vencimiento, c.asignado,
            e.alias AS empresa, e.ruc, e.id AS empresa_id,
            t.nombre_tarea AS tarea, t.id AS tarea_id
        FROM cronograma_pdt c
        JOIN empresas e ON c.empresa_id = e.id
        JOIN tareas   t ON c.tarea_id   = t.id
        WHERE EXTRACT(YEAR  FROM c.fecha_vencimiento) = %s
          AND EXTRACT(MONTH FROM c.fecha_vencimiento) = %s
        ORDER BY c.fecha_vencimiento ASC, e.alias ASC
    """, (anio, mes))
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


# ================================================================
#  VISTA PRINCIPAL
# ================================================================

def admin_radmin_cronograma():

    st.markdown("""
    <div style="margin-bottom:24px;">
        <h2 style="color:#f6c27d;font-size:22px;font-weight:800;margin:0;">Cronograma de Tareas</h2>
        <p style="color:rgba(255,255,255,0.5);font-size:13px;margin-top:4px;">
            Importa el cronograma SUNAT desde PDF · Vista por fecha de vencimiento · Asigna trabajadores
        </p>
    </div>
    """, unsafe_allow_html=True)

    for key, val in [
        ("cron_msg",          None),
        ("cron_asig_id",      None),
        ("cron_asig_open",    False),
        ("cron_preview",      None),
        ("cron_tarea_id",     None),
        ("cron_anio_import",  None),
        ("cron_meses_import", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = val

    if st.session_state.cron_msg:
        tipo, texto = st.session_state.cron_msg
        (st.success if tipo == "ok" else st.error)(texto)
        st.session_state.cron_msg = None

    hoy = date.today()

    tab_cal, tab_import = st.tabs(["Calendario", "Importar PDF"])

    # ================================================================
    #  TAB IMPORTAR PDF
    # ================================================================
    with tab_import:
        st.markdown("""
        <div style="background:rgba(93,202,165,0.06);border:1px solid rgba(93,202,165,0.2);
                    border-radius:16px;padding:20px 24px;margin-bottom:20px;">
            <h4 style="color:#5DCAA5;margin:0 0 8px;">Importar Cronograma SUNAT desde PDF</h4>
            <p style="color:rgba(255,255,255,0.5);font-size:12px;margin:0;">
                Sube el PDF del cronograma SUNAT. El sistema leerá las fechas de vencimiento
                y las cruzará con el RUC de cada empresa activa.
            </p>
        </div>
        """, unsafe_allow_html=True)

        tareas  = _get_tareas()
        tar_map = {f"[{t['nombre_proyecto']}] {t['nombre_tarea']}": t["id"] for t in tareas}

        col1, col2 = st.columns(2)
        with col1:
            tar_sel = st.selectbox("Tarea a asignar *", list(tar_map.keys()), key="import_tar")
        with col2:
            anio_import = st.selectbox(
                "Año del cronograma *",
                options=list(range(2024, 2030)),
                index=list(range(2024, 2030)).index(hoy.year),
                key="import_anio"
            )

        meses_import = st.multiselect(
            "Períodos a importar *",
            options=list(range(1, 13)),
            default=[hoy.month],
            format_func=lambda m: MESES_ES[m],
            key="import_meses"
        )

        pdf_file = st.file_uploader(
            "Selecciona el PDF del cronograma SUNAT",
            type=["pdf"],
            key="pdf_uploader"
        )

        if pdf_file and tar_sel and meses_import:
            if st.button("Leer PDF y generar vista previa", use_container_width=True,
                         key="btn_leer_pdf"):
                try:
                    cronograma_pdf = _leer_cronograma_pdf(pdf_file.read())
                    empresas       = _get_empresas_activas()
                    tarea_id       = tar_map[tar_sel]

                    filas_preview = []
                    for mes in sorted(meses_import):
                        for emp in empresas:
                            fecha_venc = _get_fecha_vencimiento_from_cron(
                                emp["ruc"], cronograma_pdf, anio_import, mes
                            )
                            if not fecha_venc:
                                continue
                            ya_existe = _ya_existe_cronograma(emp["id"], tarea_id, anio_import, mes)
                            filas_preview.append({
                                "Período":        f"{MESES_ES[mes]} {anio_import}",
                                "Empresa":        emp["alias"],
                                "RUC":            emp["ruc"],
                                "Últ. dígito":    emp["ruc"][-1] if emp["ruc"] else "?",
                                "F. Vencimiento": fecha_venc.strftime("%d/%m/%Y"),
                                "Estado":         "Ya existe" if ya_existe else "Nuevo",
                                "_empresa_id":    emp["id"],
                                "_tarea_id":      tarea_id,
                                "_mes":           mes,
                                "_anio":          anio_import,
                                "_fecha":         fecha_venc,
                                "_existe":        ya_existe,
                            })

                    st.session_state.cron_preview      = filas_preview
                    st.session_state.cron_tarea_id     = tarea_id
                    st.session_state.cron_anio_import  = anio_import
                    st.session_state.cron_meses_import = meses_import

                    if not filas_preview:
                        st.warning("No se encontraron coincidencias entre el PDF y las empresas activas.")

                except Exception as ex:
                    st.error(f"Error al leer el PDF: {ex}")

        if st.session_state.cron_preview:
            import pandas as pd
            filas   = st.session_state.cron_preview
            nuevos  = [f for f in filas if not f["_existe"]]
            ya_hay  = [f for f in filas if f["_existe"]]

            df_prev = pd.DataFrame([
                {k: v for k, v in f.items() if not k.startswith("_")}
                for f in filas
            ])

            st.markdown(f"**Vista previa — {len(filas)} registros:**")
            st.dataframe(df_prev, use_container_width=True, hide_index=True)

            ci1, ci2 = st.columns(2)
            ci1.markdown(f"<span style='color:#5DCAA5;font-size:12px;'>{len(nuevos)} nuevos a insertar</span>", unsafe_allow_html=True)
            ci2.markdown(f"<span style='color:#f6c27d;font-size:12px;'>{len(ya_hay)} ya existentes (se omitirán)</span>", unsafe_allow_html=True)

            if nuevos:
                if st.button("Confirmar importación", type="primary",
                             use_container_width=True, key="btn_confirmar_import"):
                    filas_bd = [{
                        "tarea_id":          f["_tarea_id"],
                        "empresa_id":        f["_empresa_id"],
                        "periodo_mes":       f["_mes"],
                        "periodo_anio":      f["_anio"],
                        "fecha_vencimiento": f["_fecha"],
                    } for f in nuevos]

                    ok_c, err_c, errs = _insertar_cronograma_bulk(filas_bd)

                    if ok_c:
                        st.session_state.cron_msg     = ("ok", f"{ok_c} registros importados correctamente.")
                        st.session_state.cron_preview = None
                    if err_c:
                        st.session_state.cron_msg = ("error", f"{err_c} errores: {' | '.join(errs[:3])}")
                    st.rerun()
            else:
                st.info("Todos los registros ya existen para los períodos seleccionados.")

            if st.button("Limpiar vista previa", key="btn_limpiar_preview"):
                st.session_state.cron_preview = None
                st.rerun()

    # ================================================================
    #  TAB CALENDARIO
    # ================================================================
    with tab_cal:

        col_mes, col_anio, col_spacer = st.columns([2, 1, 4])
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
                El calendario muestra empresas por su <b>fecha de vencimiento</b>.
                Ej: periodo Enero 2026 vence en Febrero 2026 · periodo Diciembre 2026 vence en Enero 2027.
            </span>
        </div>
        """, unsafe_allow_html=True)

        # ✅ QUERY CORREGIDA: usa fecha_vencimiento
        registros = _get_cronograma_mes(anio_sel, mes_sel)

        reg_por_dia: dict[int, list] = {}
        for r in registros:
            d = r["fecha_vencimiento"].day
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
                — fechas de vencimiento
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

        for semana in semanas:
            cols = st.columns(7)
            for col_idx, dia in enumerate(semana):
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
                        chips_html += (
                            f'<div style="background:rgba(255,255,255,0.04);border-left:3px solid {c};'
                            f'padding:2px 5px;border-radius:0 4px 4px 0;margin-bottom:2px;'
                            f'font-size:9px;color:rgba(255,255,255,0.8);white-space:nowrap;'
                            f'overflow:hidden;text-overflow:ellipsis;">'
                            f'{empresa}</div>'
                        )
                    if len(regs_dia) > 3:
                        chips_html += (
                            f'<div style="color:rgba(255,255,255,0.35);font-size:9px;'
                            f'padding-left:4px;">+{len(regs_dia)-3} mas</div>'
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

        # ================================================================
        #  TABLA DETALLE + ASIGNAR TRABAJADOR
        # ================================================================
        if registros:
            st.markdown(f"""
            <div style="margin-bottom:12px;">
                <span style="color:rgba(255,255,255,0.6);font-size:14px;font-weight:600;">
                    Vencimientos en {MESES_ES[mes_sel]} {anio_sel}
                </span>
            </div>
            """, unsafe_allow_html=True)

            cols_h2 = st.columns([0.4, 0.9, 1.1, 0.8, 1, 1, 0.8, 1])
            for col, h in zip(cols_h2, ["DIA", "PERIODO", "EMPRESA", "RUC", "TAREA", "F. VENC.", "ESTADO", "ACCION"]):
                col.markdown(
                    f"<span style='color:rgba(255,255,255,0.4);font-size:10px;"
                    f"font-weight:700;letter-spacing:1px;'>{h}</span>",
                    unsafe_allow_html=True
                )
            st.divider()

            for r in registros:
                with st.container(border=True):
                    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([0.4, 0.9, 1.1, 0.8, 1, 1, 0.8, 1])

                    c1.markdown(
                        f"<span style='color:#f6c27d;font-weight:700;'>{r['fecha_vencimiento'].day}</span>",
                        unsafe_allow_html=True
                    )
                    c2.markdown(
                        f"<span style='color:rgba(255,255,255,0.45);font-size:11px;'>"
                        f"{MESES_ES[r['periodo_mes']]} {r['periodo_anio']}</span>",
                        unsafe_allow_html=True
                    )
                    c3.markdown(
                        f"<span style='color:white;font-size:12px;'>{r['empresa']}</span>",
                        unsafe_allow_html=True
                    )
                    c4.markdown(
                        f"<span style='color:rgba(255,255,255,0.5);font-size:11px;'>{r['ruc']}</span>",
                        unsafe_allow_html=True
                    )
                    c5.markdown(
                        f"<span style='color:rgba(255,255,255,0.7);font-size:12px;'>{r['tarea']}</span>",
                        unsafe_allow_html=True
                    )
                    c6.markdown(
                        f"<span style='color:rgba(255,255,255,0.7);font-size:12px;'>"
                        f"{r['fecha_vencimiento'].strftime('%d/%m/%Y')}</span>",
                        unsafe_allow_html=True
                    )
                    c7.markdown(_badge_asignado(r["asignado"]), unsafe_allow_html=True)

                    with c8:
                        if not r["asignado"]:
                            if st.button("Asignar", key=f"asig_{r['id']}", use_container_width=True):
                                st.session_state.cron_asig_id   = r["id"]
                                st.session_state.cron_asig_open = True
                                st.rerun()
                        else:
                            st.markdown(
                                "<span style='color:rgba(255,255,255,0.3);font-size:11px;'>listo</span>",
                                unsafe_allow_html=True
                            )

                # Panel asignar trabajador
                if st.session_state.cron_asig_open and st.session_state.cron_asig_id == r["id"]:
                    st.markdown(f"""
                    <div style="background:rgba(133,183,235,0.06);border:1px solid rgba(133,183,235,0.2);
                                border-radius:16px;padding:20px 24px;margin:4px 0 12px;">
                        <h4 style="color:#85B7EB;margin:0 0 4px;">
                            Asignar — {r['empresa']}
                        </h4>
                        <p style="color:rgba(255,255,255,0.4);font-size:12px;margin:0;">
                            Periodo: {MESES_ES[r['periodo_mes']]} {r['periodo_anio']} ·
                            Vence: {r['fecha_vencimiento'].strftime('%d/%m/%Y')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    usuarios = _get_usuarios_activos()
                    usr_map  = {f"{u['nom_res']} ({u['alias']})": u["id"] for u in usuarios}

                    col_u, col_p = st.columns(2)
                    with col_u:
                        usr_sel = st.multiselect(
                            "Trabajador(es) *",
                            list(usr_map.keys()),
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
                                    cronograma_id     = r["id"],
                                    usuario_ids       = uid_list,
                                    empresa_id        = r["empresa_id"],
                                    tarea_id          = r["tarea_id"],
                                    fecha_vencimiento = r["fecha_vencimiento"],
                                    peso              = peso,
                                )
                                if ok:
                                    st.session_state.cron_msg       = ("ok", f"Asignacion #{result} creada.")
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
                f"Ve a 'Importar PDF' para cargar el cronograma SUNAT."
            )