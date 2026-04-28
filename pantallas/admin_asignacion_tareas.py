import streamlit as st
from config.db import get_connection
from datetime import date
import pandas as pd
import io


# ================================================================
#  REPOSITORIO
# ================================================================

def _get_usuarios_activos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nom_res, alias
        FROM usuarios
        WHERE estado = 'activo' AND rol = 'trabajador'
        ORDER BY nom_res
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_empresas_activas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, razon_social, alias, ruc
        FROM empresas
        WHERE estado_contrato = 'Activo'
        ORDER BY razon_social
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_proyectos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_proyecto FROM proyectos ORDER BY nombre_proyecto")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_tareas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id, t.nombre_tarea, t.proyecto_id, p.nombre_proyecto
        FROM tareas t
        JOIN proyectos p ON t.proyecto_id = p.id
        ORDER BY p.nombre_proyecto, t.nombre_tarea
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_asignaciones(mes=None, anio=None, solo_completadas=False):
    conn = get_connection()
    cur = conn.cursor()

    where_clauses = []
    params = []

    if solo_completadas:
        where_clauses.append("a.estado = 'completada'")

    if mes and anio:
        where_clauses.append("MONTH(a.fecha_meta) = %s AND YEAR(a.fecha_meta) = %s")
        params.extend([mes, anio])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cur.execute(f"""
        SELECT
            a.id,
            u.nom_res       AS trabajador,
            u.alias         AS alias,
            e.razon_social  AS empresa,
            t.nombre_tarea  AS tarea,
            p.nombre_proyecto AS proyecto,
            a.fecha_meta,
            a.estado,
            a.fecha_creacion,
            COALESCE(rt.fecha_realizada, NULL) AS fecha_realizada
        FROM asignaciones a
        JOIN usuarios u  ON a.usuario_id  = u.id
        JOIN empresas e  ON a.empresa_id  = e.id
        JOIN tareas   t  ON a.tarea_id    = t.id
        JOIN proyectos p ON t.proyecto_id = p.id
        LEFT JOIN registros_tareas rt ON a.id = rt.asignacion_id
        {where_sql}
        ORDER BY a.fecha_meta ASC, a.id DESC
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_asignacion_by_id(aid: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM asignaciones WHERE id = %s", (aid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def _crear_asignacion(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO asignaciones (usuario_id, empresa_id, tarea_id, fecha_meta, estado)
        VALUES (%s, %s, %s, %s, 'pendiente')
    """, (data["usuario_id"], data["empresa_id"], data["tarea_id"], data["fecha_meta"]))
    conn.commit()
    cur.close(); conn.close()


def _actualizar_asignacion(aid: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE asignaciones
        SET usuario_id=%s, empresa_id=%s, tarea_id=%s, fecha_meta=%s, estado=%s
        WHERE id=%s
    """, (data["usuario_id"], data["empresa_id"], data["tarea_id"],
          data["fecha_meta"], data["estado"], aid))
    conn.commit()
    cur.close(); conn.close()


def _eliminar_asignacion(aid: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM asignaciones WHERE id = %s", (aid,))
    conn.commit()
    cur.close(); conn.close()


def _insertar_asignacion_bulk(usuario_id, empresa_id, tarea_id, fecha_meta, fecha_realizada, rendimiento):
    """Inserta asignación y su registro_tarea en bloque (importación Excel)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1) Crear la asignación como completada
        cur.execute("""
            INSERT INTO asignaciones (usuario_id, empresa_id, tarea_id, fecha_meta, estado)
            VALUES (%s, %s, %s, %s, 'completada')
        """, (usuario_id, empresa_id, tarea_id, fecha_meta))
        asignacion_id = cur.lastrowid

        # 2) Registrar en registros_tareas
        cur.execute("""
            INSERT INTO registros_tareas (asignacion_id, fecha_realizada, rendimiento)
            VALUES (%s, %s, %s)
        """, (asignacion_id, fecha_realizada, rendimiento))

        conn.commit()
        return True, None
    except Exception as ex:
        conn.rollback()
        return False, str(ex)
    finally:
        cur.close(); conn.close()


# ================================================================
#  HELPERS UI
# ================================================================

def _badge_estado(estado: str) -> str:
    cfg = {
        "pendiente":  ("rgba(246,194,125,0.15)", "#f6c27d",  "PENDIENTE"),
        "completada": ("rgba(93,202,165,0.15)",  "#5DCAA5",  "COMPLETADA"),
        "vencida":    ("rgba(240,149,149,0.15)", "#F09595",  "VENCIDA"),
    }
    bg, color, label = cfg.get(estado, ("rgba(255,255,255,0.08)", "white", estado.upper()))
    return f'<span style="background:{bg};color:{color};padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;">{label}</span>'


def _badge_rendimiento(rendimiento: str) -> str:
    cfg = {
        "OPTIMO":   ("rgba(93,202,165,0.15)",  "#5DCAA5"),
        "MEDIO":    ("rgba(246,194,125,0.15)", "#f6c27d"),
        "BAJO":     ("rgba(240,149,149,0.15)", "#F09595"),
        "URGENTE":  ("rgba(220,100,100,0.20)", "#e06060"),
    }
    bg, color = cfg.get(rendimiento, ("rgba(255,255,255,0.08)", "white"))
    return f'<span style="background:{bg};color:{color};padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700;">{rendimiento}</span>'


def _alerta_fecha(fecha_meta, estado: str = None) -> str:
    if not fecha_meta:
        return ""
    hoy = date.today()
    if isinstance(fecha_meta, str):
        from datetime import datetime
        fecha_meta = datetime.strptime(fecha_meta, "%Y-%m-%d").date()
    
    # Si está completada, no mostrar alerta de vencimiento
    if estado == "completada":
        return ""
    
    diff = (fecha_meta - hoy).days
    if diff < 0:
        return ' <span style="color:#F09595;font-size:11px;">⚠ vencida</span>'
    if diff == 0:
        return ' <span style="color:#f6c27d;font-size:11px;">⚡ hoy</span>'
    if diff <= 3:
        return f' <span style="color:#f6c27d;font-size:11px;">⏰ {diff}d</span>'
    return ""


def _form_asignacion(prefill: dict = None, key_prefix: str = "new"):
    usuarios = _get_usuarios_activos()
    empresas = _get_empresas_activas()
    tareas   = _get_tareas()

    usr_map = {f"{u['nom_res']} ({u['alias']})": u["id"] for u in usuarios}
    emp_map = {f"{e['razon_social']} — {e['ruc']}": e["id"] for e in empresas}
    tar_map = {f"[{t['nombre_proyecto']}] {t['nombre_tarea']}": t["id"] for t in tareas}

    usr_names = list(usr_map.keys())
    emp_names = list(emp_map.keys())
    tar_names = list(tar_map.keys())

    usr_default = emp_default = tar_default = 0

    if prefill:
        uid = prefill.get("usuario_id")
        eid = prefill.get("empresa_id")
        tid = prefill.get("tarea_id")
        for i, u in enumerate(usuarios):
            if u["id"] == uid:
                usr_default = i; break
        for i, e in enumerate(empresas):
            if e["id"] == eid:
                emp_default = i; break
        for i, t in enumerate(tareas):
            if t["id"] == tid:
                tar_default = i; break

    col1, col2 = st.columns(2)

    with col1:
        usr_sel = st.selectbox("Trabajador *", usr_names,
                               index=usr_default, key=f"{key_prefix}_usr")
        tar_sel = st.selectbox("Tarea *", tar_names,
                               index=tar_default, key=f"{key_prefix}_tar")

    with col2:
        emp_sel = st.selectbox("Empresa *", emp_names,
                               index=emp_default, key=f"{key_prefix}_emp")

        fecha_default = prefill["fecha_meta"] if prefill and prefill.get("fecha_meta") else date.today()
        if isinstance(fecha_default, str):
            from datetime import datetime
            fecha_default = datetime.strptime(fecha_default, "%Y-%m-%d").date()

        fecha_meta = st.date_input("Fecha meta *", value=fecha_default,
                                   format="DD/MM/YYYY", key=f"{key_prefix}_fecha")

    estado = "pendiente"
    if prefill:
        estado = st.selectbox("Estado", ["pendiente", "completada", "vencida"],
                              index=["pendiente", "completada", "vencida"].index(
                                  prefill.get("estado", "pendiente")),
                              key=f"{key_prefix}_estado")

    return {
        "usuario_id": usr_map.get(usr_sel),
        "empresa_id": emp_map.get(emp_sel),
        "tarea_id":   tar_map.get(tar_sel),
        "fecha_meta": fecha_meta,
        "estado":     estado,
        "_trabajador": usr_sel,
        "_tarea":      tar_sel,
    }


# ================================================================
#  IMPORTACIÓN EXCEL
# ================================================================

def _seccion_importar_excel():
    """
    Estructura esperada del Excel (columnas en orden o por nombre):
    EMPRESA | PROYECTO | TAREA | ENCARGADO | FECHA REALIZADA | FECHA META | CANT | PRIORIDAD

    - EMPRESA   → alias de la empresa  (ej: IENSA, GG & A P I)
    - PROYECTO  → nombre del proyecto  (ej: PLAME, DJ)
    - TAREA     → número de tarea dentro del proyecto (id relativo, 1..N)
    - ENCARGADO → id del usuario       (ej: 3, 15)
    - FECHA REALIZADA → dd/mm/yyyy
    - FECHA META      → dd/mm/yyyy
    - CANT      → peso (ignorado en inserción pero se valida)
    - PRIORIDAD → BAJO | MEDIO | OPTIMO | URGENTE  → rendimiento
    """

    st.markdown("""
    <div style="background:rgba(93,202,165,0.06);border:1px solid rgba(93,202,165,0.2);
                border-radius:16px;padding:20px 24px;margin-bottom:20px;">
        <h4 style="color:#5DCAA5;margin:0 0 8px;">📥 Importar desde Excel</h4>
        <p style="color:rgba(255,255,255,0.5);font-size:12px;margin:0;">
            Columnas requeridas: <b>EMPRESA · PROYECTO · TAREA · ENCARGADO ·
            FECHA REALIZADA · FECHA META · CANT · PRIORIDAD</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Descargar plantilla ──────────────────────────────────────
    plantilla = pd.DataFrame(columns=[
        "EMPRESA", "PROYECTO", "TAREA", "ENCARGADO",
        "FECHA REALIZADA", "FECHA META", "CANT", "PRIORIDAD"
    ])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        plantilla.to_excel(writer, index=False, sheet_name="Importar")
    buf.seek(0)
    st.download_button("⬇ Descargar plantilla", data=buf,
                       file_name="plantilla_asignaciones.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    archivo = st.file_uploader("Selecciona el archivo Excel", type=["xlsx", "xls"],
                               key="excel_uploader")
    if not archivo:
        return

    try:
        df = pd.read_excel(archivo)
    except Exception as ex:
        st.error(f"No se pudo leer el archivo: {ex}")
        return

    # Normalizar nombres de columna
    df.columns = [c.strip().upper() for c in df.columns]

    required_cols = {"EMPRESA", "TAREA", "ENCARGADO",
                     "FECHA REALIZADA", "FECHA META", "CANT", "PRIORIDAD"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Faltan columnas: {', '.join(missing)}")
        return

    # Cargar catálogos para resolución de IDs
    empresas   = _get_empresas_activas()
    tareas_db  = _get_tareas()
    proyectos  = _get_proyectos()
    usuarios   = _get_usuarios_activos()
    # MAPAS DE BÚSQUEDA
    emp_alias_map = {
        e["alias"].strip().upper(): e["id"]
        for e in empresas
    }

    proy_map = {
        int(p["id"]): int(p["id"])
        for p in proyectos
    }

    usr_id_set = {
        int(u["id"])
        for u in usuarios
    }

    # ============================================================
    # MAPEO GLOBAL DE TAREAS USANDO EL ID REAL
    # ============================================================
    tarea_por_numero = {}
    proyecto_por_tarea = {}

    for tarea in tareas_db:
        tarea_id = int(tarea["id"])

        # El número de tarea del Excel será exactamente el ID
        tarea_por_numero[tarea_id] = tarea_id
        proyecto_por_tarea[tarea_id] = int(tarea["proyecto_id"])

    RENDIMIENTOS_VALIDOS = {"BAJO", "MEDIO", "OPTIMO", "URGENTE"}

    errores_import  = []
    filas_validas   = []
    
    for i, row in df.iterrows():
        fila_num = i + 2  # fila Excel (1-indexed + header)
        errores_fila = []

        empresa_alias = str(row.get("EMPRESA", "")).strip().upper()

        tarea_num_raw = row.get("TAREA")
        encargado_raw = row.get("ENCARGADO")
        fecha_real_raw = row.get("FECHA REALIZADA")
        fecha_meta_raw = row.get("FECHA META")
        prioridad_raw  = str(row.get("PRIORIDAD", "")).strip().upper()

        # ── Resolver EMPRESA ────────────────────────────────────
        empresa_id = emp_alias_map.get(empresa_alias)
        if not empresa_id:
            errores_fila.append(f"Empresa '{empresa_alias}' no encontrada")

        # ── Resolver TAREA ──────────────────────────────────────
        tarea_id = None
        proyecto_id = None
        try:
            tarea_num = int(tarea_num_raw)
            tarea_id = tarea_por_numero.get(tarea_num)
            
            if not tarea_id:
                errores_fila.append(
                    f"TAREA {tarea_num} no existe"
                )
            else:
                proyecto_id = proyecto_por_tarea[tarea_id]
        except (TypeError, ValueError):
            errores_fila.append(f"TAREA debe ser un número entero (valor: {tarea_num_raw})")

        # ── Resolver ENCARGADO ──────────────────────────────────
        usuario_id = None
        try:
            uid = int(encargado_raw)
            if uid in usr_id_set:
                usuario_id = uid
            else:
                errores_fila.append(f"Usuario ID {uid} no existe o no está activo")
        except (TypeError, ValueError):
            errores_fila.append(f"ENCARGADO debe ser un ID numérico (valor: {encargado_raw})")

        # ── Parsear FECHAS ──────────────────────────────────────
        from datetime import datetime as dt

        def parse_fecha(val):
            if pd.isna(val) if hasattr(val, '__class__') and val.__class__.__name__ in ('float','NaTType') else False:
                return None
            if isinstance(val, (date,)):
                return val
            if hasattr(val, 'date'):
                return val.date()
            try:
                return dt.strptime(str(val).strip(), "%d/%m/%Y").date()
            except Exception:
                try:
                    return dt.strptime(str(val).strip(), "%Y-%m-%d").date()
                except Exception:
                    return None

        fecha_realizada = parse_fecha(fecha_real_raw)
        fecha_meta      = parse_fecha(fecha_meta_raw)

        if not fecha_realizada:
            errores_fila.append(f"FECHA REALIZADA inválida (valor: {fecha_real_raw})")
        if not fecha_meta:
            errores_fila.append(f"FECHA META inválida (valor: {fecha_meta_raw})")

        # ── Resolver PRIORIDAD → rendimiento ────────────────────
        rendimiento = prioridad_raw if prioridad_raw in RENDIMIENTOS_VALIDOS else None
        if not rendimiento:
            errores_fila.append(f"PRIORIDAD '{prioridad_raw}' no válida (BAJO/MEDIO/OPTIMO/URGENTE)")

        # ── Validar que tarea_id está resuelto ───────────────────
        if not tarea_id:
            errores_fila.append("No se pudo resolver TAREA_ID")

        # ── Acumular ────────────────────────────────────────────
        if errores_fila:
            errores_import.append((fila_num, errores_fila))
        else:
            filas_validas.append({
                "fila":          fila_num,
                "usuario_id":    usuario_id,
                "empresa_id":    empresa_id,
                "tarea_id":      tarea_id,
                "fecha_meta":    fecha_meta,
                "fecha_realizada": fecha_realizada,
                "rendimiento":   rendimiento,
            })

    # ── Reporte de errores ───────────────────────────────────────
    if errores_import:
        with st.expander(f"⚠ {len(errores_import)} fila(s) con errores (no se importarán)", expanded=True):
            for fila_num, errs in errores_import:
                st.markdown(f"**Fila {fila_num}:** " + " · ".join(errs))

    if not filas_validas:
        st.warning("No hay filas válidas para importar.")
        return

    st.success(f"✅ {len(filas_validas)} fila(s) listas para importar.")

    # ── Vista previa ─────────────────────────────────────────────
    with st.expander("👁 Vista previa de filas válidas"):
        preview_rows = []
        usr_map_id   = {u["id"]: f"{u['nom_res']} ({u['alias']})" for u in usuarios}
        emp_map_id   = {e["id"]: e["alias"] for e in empresas}
        tar_map_id   = {t["id"]: t["nombre_tarea"] for t in tareas_db}

        for f in filas_validas:
            preview_rows.append({
                "Fila":       f["fila"],
                "Trabajador": usr_map_id.get(f["usuario_id"], f["usuario_id"]),
                "Empresa":    emp_map_id.get(f["empresa_id"], f["empresa_id"]),
                "Tarea":      tar_map_id.get(f["tarea_id"], f["tarea_id"]),
                "F. Meta":    f["fecha_meta"],
                "F. Real.":   f["fecha_realizada"],
                "Rendimiento": f["rendimiento"],
            })
        st.dataframe(pd.DataFrame(preview_rows), use_container_width=True)

    # ── Botón confirmar importación ──────────────────────────────
    if st.button("📥 Confirmar importación", type="primary", use_container_width=True,
                 key="btn_confirmar_import"):
        ok_count = err_count = 0
        for f in filas_validas:
            ok, err = _insertar_asignacion_bulk(
                f["usuario_id"], f["empresa_id"], f["tarea_id"],
                f["fecha_meta"], f["fecha_realizada"], f["rendimiento"]
            )
            if ok:
                ok_count += 1
            else:
                err_count += 1
                st.error(f"Fila {f['fila']}: {err}")

        if ok_count:
            st.session_state.asig_msg = ("ok", f"✅ {ok_count} asignación(es) importada(s) correctamente.")
        if err_count:
            st.session_state.asig_msg = ("error", f"⚠ {err_count} fila(s) fallaron al insertar.")
        st.rerun()


# ================================================================
#  VISTA PRINCIPAL
# ================================================================

def admin_asignacion_tarea():

    st.markdown("""
    <div style="margin-bottom:24px;">
        <h2 style="color:#f6c27d;font-size:22px;font-weight:800;margin:0;">Asignación de Tareas</h2>
        <p style="color:rgba(255,255,255,0.5);font-size:13px;margin-top:4px;">
            Asigna tareas a trabajadores por empresa y fecha meta
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Inicializar estados ──────────────────────────────────────
    for key in ["asig_modo", "asig_id_editar", "asig_id_eliminar", "asig_msg", "asig_pagina_actual"]:
        if key not in st.session_state:
            st.session_state[key] = None if key != "asig_pagina_actual" else 1

    # ── Mensaje de feedback ──────────────────────────────────────
    if st.session_state.asig_msg:
        tipo, texto = st.session_state.asig_msg
        (st.success if tipo == "ok" else st.error)(texto)
        st.session_state.asig_msg = None

    # ── Tabs principales ─────────────────────────────────────────
    tab_lista, tab_import = st.tabs(["📋 Asignaciones", "📥 Importar Excel"])

    # ================================================================
    #  TAB IMPORTAR EXCEL
    # ================================================================
    with tab_import:
        _seccion_importar_excel()

    # ================================================================
    #  TAB LISTA DE ASIGNACIONES
    # ================================================================
    with tab_lista:

        # ── Filtros superiores ───────────────────────────────────
        st.markdown("### 🔍 Filtros", help="Utiliza los filtros para buscar y organizar las asignaciones")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            filtro_texto = st.text_input(
                "🔎 Buscar por trabajador, empresa o tarea",
                placeholder="Escribe aquí...",
                label_visibility="collapsed"
            )
        
        with col_f2:
            filtro_estado = st.selectbox(
                "Estado",
                ["📊 Todos", "⏳ Pendientes", "✅ Completadas", "⚠️ Vencidas"],
                index=0,
                label_visibility="collapsed"
            )
        
        with col_f3:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            filtrar_por_fecha = st.checkbox("📅 Por mes/año")
        
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── Selector Mes / Año ────────────────────────────────────
        filtro_mes = filtro_anio = None
        if filtrar_por_fecha:
            hoy = date.today()
            meses = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            col_m, col_a = st.columns(2)
            with col_m:
                filtro_mes = st.selectbox(
                    "Mes", options=list(meses.keys()),
                    format_func=lambda m: meses[m],
                    index=hoy.month - 1,
                    key="filtro_mes"
                )
            with col_a:
                filtro_anio = st.selectbox(
                    "Año", options=list(range(2022, hoy.year + 2)),
                    index=list(range(2022, hoy.year + 2)).index(hoy.year),
                    key="filtro_anio"
                )
        
        col_btn_crear = st.columns(4)[3]
        with col_btn_crear:
            if st.button("➕ Nueva asignación", use_container_width=True):
                st.session_state.asig_modo      = "crear"
                st.session_state.asig_id_editar = None

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # ================================================================
        #  FORMULARIO CREAR
        # ================================================================
        if st.session_state.asig_modo == "crear":
            st.markdown("""
            <div style="background:rgba(246,194,125,0.06);border:1px solid rgba(246,194,125,0.2);
                        border-radius:16px;padding:20px 24px;margin-bottom:20px;">
                <h4 style="color:#f6c27d;margin:0 0 16px;">Nueva asignación</h4>
            </div>
            """, unsafe_allow_html=True)

            datos = _form_asignacion(key_prefix="crear")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Guardar", use_container_width=True, key="btn_crear_asig"):
                    errores = []
                    if not datos["usuario_id"]: errores.append("Selecciona un trabajador.")
                    if not datos["empresa_id"]: errores.append("Selecciona una empresa.")
                    if not datos["tarea_id"]:   errores.append("Selecciona una tarea.")
                    if not datos["fecha_meta"]: errores.append("Ingresa una fecha meta.")

                    if errores:
                        st.session_state.asig_msg = ("error", " | ".join(errores))
                    else:
                        try:
                            _crear_asignacion(datos)
                            st.session_state.asig_msg  = ("ok", f"✅ Tarea '{datos['_tarea']}' asignada a {datos['_trabajador']}.")
                            st.session_state.asig_modo = None
                        except Exception as ex:
                            st.session_state.asig_msg = ("error", f"Error al guardar: {ex}")
                    st.rerun()
            with c2:
                if st.button("✖ Cancelar", use_container_width=True, key="btn_cancel_crear_asig"):
                    st.session_state.asig_modo = None
                    st.rerun()

        # ================================================================
        #  TABLA DE ASIGNACIONES
        # ================================================================
        solo_completadas = filtrar_por_fecha
        asignaciones = _get_asignaciones(
            mes=filtro_mes,
            anio=filtro_anio,
            solo_completadas=solo_completadas
        )

        # Mapear valores de filtro a internos
        estado_map = {
            "📊 Todos": "Todos",
            "⏳ Pendientes": "pendiente",
            "✅ Completadas": "completada",
            "⚠️ Vencidas": "vencida"
        }
        filtro_estado_interno = estado_map.get(filtro_estado, "Todos")

        # Filtros en memoria
        if filtro_texto:
            q = filtro_texto.lower()
            asignaciones = [a for a in asignaciones if
                            q in a["tarea"].lower() or
                            q in a["empresa"].lower() or
                            q in a["trabajador"].lower()]

        if filtro_estado_interno != "Todos":
            asignaciones = [a for a in asignaciones if a["estado"] == filtro_estado_interno]

        # Contador resumen
        total       = len(asignaciones)
        pendientes  = sum(1 for a in asignaciones if a["estado"] == "pendiente")
        vencidas    = sum(1 for a in asignaciones if a["estado"] == "vencida")
        completadas = sum(1 for a in asignaciones if a["estado"] == "completada")

        m1, m2, m3, m4 = st.columns(4)
        for col, label, val, color in [
            (m1, "Total",       total,       "white"),
            (m2, "Pendientes",  pendientes,  "#f6c27d"),
            (m3, "Vencidas",    vencidas,    "#F09595"),
            (m4, "Completadas", completadas, "#5DCAA5"),
        ]:
            col.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
                        border-radius:12px;padding:12px 16px;margin-bottom:16px;">
                <div style="color:rgba(255,255,255,0.4);font-size:10px;letter-spacing:1px;
                            text-transform:uppercase;margin-bottom:4px;">{label}</div>
                <div style="color:{color};font-size:22px;font-weight:800;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

        if not asignaciones:
            st.info("No hay asignaciones que mostrar.")
            return

        # ── PAGINACIÓN ───────────────────────────────────────────
        REGISTROS_POR_PAGINA = 15
        total_paginas = (len(asignaciones) + REGISTROS_POR_PAGINA - 1) // REGISTROS_POR_PAGINA
        
        if "asig_pagina_actual" not in st.session_state:
            st.session_state.asig_pagina_actual = 1
        
        # Validar página actual
        if st.session_state.asig_pagina_actual > total_paginas:
            st.session_state.asig_pagina_actual = total_paginas
        if st.session_state.asig_pagina_actual < 1:
            st.session_state.asig_pagina_actual = 1
        
        pagina_actual = st.session_state.asig_pagina_actual
        inicio = (pagina_actual - 1) * REGISTROS_POR_PAGINA
        fin = inicio + REGISTROS_POR_PAGINA
        asignaciones_pagina = asignaciones[inicio:fin]

        # Cabecera tabla
        st.markdown("""
        <div style="display:grid;grid-template-columns:0.8fr 1.4fr 1.4fr 1fr 1.1fr 1.1fr 1.1fr 80px;
                    gap:8px;padding:8px 16px;
                    color:rgba(255,255,255,0.4);font-size:10px;
                    letter-spacing:1px;text-transform:uppercase;
                    border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:4px;">
            <span>Trabajador</span>
            <span>Empresa</span>
            <span>Tarea</span>
            <span>Proyecto</span>
            <span>F. Meta</span>
            <span>F. Realizada</span>
            <span>Estado</span>
            <span></span>
        </div>
        """, unsafe_allow_html=True)

        for a in asignaciones_pagina:
            fecha_meta_str = a["fecha_meta"].strftime("%d/%m/%Y") if hasattr(a["fecha_meta"], "strftime") else str(a["fecha_meta"])
            fecha_realizada_str = "—"
            if a.get("fecha_realizada"):
                fecha_realizada_str = a["fecha_realizada"].strftime("%d/%m/%Y") if hasattr(a["fecha_realizada"], "strftime") else str(a["fecha_realizada"])
            
            alerta = _alerta_fecha(a["fecha_meta"], a["estado"])

            st.markdown(f"""
            <div style="display:grid;grid-template-columns:0.8fr 1.4fr 1.4fr 1fr 1.1fr 1.1fr 1.1fr 80px;
                        gap:8px;align-items:center;padding:12px 16px;
                        background:rgba(255,255,255,0.03);border-radius:12px;
                        border:1px solid rgba(255,255,255,0.05);margin-bottom:6px;">
                <div>
                    <span style="color:white;font-weight:600;font-size:12px;">{a['alias']}</span>
                    <span style="color:rgba(255,255,255,0.3);font-size:10px;display:block;">{a['trabajador']}</span>
                </div>
                <span style="color:rgba(255,255,255,0.7);font-size:12px;">{a['empresa']}</span>
                <span style="color:rgba(255,255,255,0.85);font-size:12px;">{a['tarea']}</span>
                <span style="color:rgba(255,255,255,0.5);font-size:11px;">{a['proyecto']}</span>
                <span style="color:rgba(255,255,255,0.7);font-size:12px;">{fecha_meta_str}{alerta}</span>
                <span style="color:rgba(255,255,255,0.6);font-size:11px;">{fecha_realizada_str}</span>
                <span>{_badge_estado(a['estado'])}</span>
                <span></span>
            </div>
            """, unsafe_allow_html=True)

            # Botones acción
            _, _, _, _, _, _, _, col_acc = st.columns([0.8, 1.4, 1.4, 1, 1.1, 1.1, 1.1, 0.9])
            with col_acc:
                ba1, ba2 = st.columns(2)
                with ba1:
                    if st.button("✏️", key=f"edit_asig_{a['id']}", help="Editar"):
                        st.session_state.asig_modo      = "editar"
                        st.session_state.asig_id_editar = a["id"]
                        st.rerun()
                with ba2:
                    if st.button("🗑️", key=f"del_asig_{a['id']}", help="Eliminar"):
                        st.session_state.asig_id_eliminar = a["id"]
                        st.rerun()

            # ── Formulario editar inline ─────────────────────────
            if st.session_state.asig_modo == "editar" and st.session_state.asig_id_editar == a["id"]:
                prefill = _get_asignacion_by_id(a["id"])
                st.markdown(f"""
                <div style="background:rgba(133,183,235,0.06);border:1px solid rgba(133,183,235,0.2);
                            border-radius:16px;padding:20px 24px;margin:8px 0 16px;">
                    <h4 style="color:#85B7EB;margin:0 0 16px;">Editando asignación #{a['id']}</h4>
                </div>
                """, unsafe_allow_html=True)

                datos = _form_asignacion(prefill=prefill, key_prefix=f"edit_asig_{a['id']}")

                e1, e2 = st.columns(2)
                with e1:
                    if st.button("💾 Actualizar", use_container_width=True, key=f"btn_upd_asig_{a['id']}"):
                        errores = []
                        if not datos["usuario_id"]: errores.append("Selecciona un trabajador.")
                        if not datos["empresa_id"]: errores.append("Selecciona una empresa.")
                        if not datos["tarea_id"]:   errores.append("Selecciona una tarea.")

                        if errores:
                            st.session_state.asig_msg = ("error", " | ".join(errores))
                        else:
                            try:
                                _actualizar_asignacion(a["id"], datos)
                                st.session_state.asig_msg       = ("ok", "✅ Asignación actualizada.")
                                st.session_state.asig_modo      = None
                                st.session_state.asig_id_editar = None
                                st.session_state.asig_pagina_actual = 1
                            except Exception as ex:
                                st.session_state.asig_msg = ("error", f"Error: {ex}")
                        st.rerun()
                with e2:
                    if st.button("✖ Cancelar", use_container_width=True, key=f"btn_cancel_edit_asig_{a['id']}"):
                        st.session_state.asig_modo      = None
                        st.session_state.asig_id_editar = None
                        st.rerun()

            # ── Confirmación eliminar ────────────────────────────
            if st.session_state.asig_id_eliminar == a["id"]:
                st.warning(f"¿Eliminar la asignación de **{a['tarea']}** para {a['alias']}?")
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("🗑️ Confirmar", use_container_width=True,
                                 key=f"confirm_del_asig_{a['id']}", type="primary"):
                        try:
                            _eliminar_asignacion(a["id"])
                            st.session_state.asig_msg         = ("ok", "✅ Asignación eliminada.")
                            st.session_state.asig_id_eliminar = None
                            st.session_state.asig_pagina_actual = 1
                        except Exception as ex:
                            st.session_state.asig_msg = ("error", f"No se puede eliminar: {ex}")
                        st.rerun()
                with d2:
                    if st.button("✖ Cancelar", use_container_width=True, key=f"cancel_del_asig_{a['id']}"):
                        st.session_state.asig_id_eliminar = None
                        st.rerun()

        # ── Controles de paginación ──────────────────────────────
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        
        col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
        
        with col_pag1:
            if st.button("← Anterior", use_container_width=True, 
                        disabled=(pagina_actual == 1)):
                st.session_state.asig_pagina_actual = pagina_actual - 1
                st.rerun()
        
        with col_pag2:
            st.markdown(f"""
            <div style="display:flex;justify-content:center;align-items:center;height:40px;">
                <span style="color:rgba(255,255,255,0.7);font-size:13px;font-weight:600;">
                    Página {pagina_actual} de {total_paginas}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        with col_pag3:
            if st.button("Siguiente →", use_container_width=True, 
                        disabled=(pagina_actual == total_paginas)):
                st.session_state.asig_pagina_actual = pagina_actual + 1
                st.rerun()