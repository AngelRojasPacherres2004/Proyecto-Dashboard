import streamlit as st
import pandas as pd
from config.db import get_connection
from datetime import date, datetime
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
    """
    Devuelve asignaciones AGRUPADAS por id.
    Cada fila representa un grupo de asignación con lista de trabajadores.
    """
    conn = get_connection()
    cur = conn.cursor()

    where_clauses = []
    params = []

    if solo_completadas:
        where_clauses.append("a.estado = 'completada'")

    if mes and anio:
        # PostgreSQL: EXTRACT en lugar de MONTH() y YEAR()
        where_clauses.append("EXTRACT(MONTH FROM a.fecha_meta) = %s AND EXTRACT(YEAR FROM a.fecha_meta) = %s")
        params.extend([mes, anio])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cur.execute(f"""
        SELECT
            a.id,
            a.usuario_id,
            u.nom_res       AS trabajador,
            u.alias         AS alias,
            e.razon_social  AS empresa,
            e.id            AS empresa_id,
            t.nombre_tarea  AS tarea,
            t.id            AS tarea_id,
            p.nombre_proyecto AS proyecto,
            a.fecha_meta,
            a.estado,
            a.fecha_creacion,
            a.peso,
            (
                SELECT rt.fecha_realizada
                FROM registros_tareas rt
                WHERE rt.asignacion_id = a.id AND rt.usuario_id = a.usuario_id
                ORDER BY rt.id DESC
                LIMIT 1
            ) AS fecha_realizada
        FROM asignaciones a
        JOIN usuarios  u ON a.usuario_id  = u.id
        JOIN empresas  e ON a.empresa_id  = e.id
        JOIN tareas    t ON a.tarea_id    = t.id
        JOIN proyectos p ON t.proyecto_id = p.id
        {where_sql}
        ORDER BY a.fecha_meta ASC, a.id ASC, a.usuario_id ASC
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()

    # ── Agrupar filas por id de asignación ──────────────────────
    grupos = {}
    for r in rows:
        aid = r["id"]
        if aid not in grupos:
            grupos[aid] = {
                "id":             aid,
                "empresa":        r["empresa"],
                "empresa_id":     r["empresa_id"],
                "tarea":          r["tarea"],
                "tarea_id":       r["tarea_id"],
                "proyecto":       r["proyecto"],
                "fecha_meta":     r["fecha_meta"],
                "estado":         r["estado"],
                "fecha_creacion": r["fecha_creacion"],
                "peso":           r["peso"],
                "trabajadores":   [],
            }
        grupos[aid]["trabajadores"].append({
            "usuario_id":      r["usuario_id"],
            "trabajador":      r["trabajador"],
            "alias":           r["alias"],
            "fecha_realizada": r["fecha_realizada"],
        })

    return list(grupos.values())


def _get_asignacion_grupo_by_id(aid: int):
    """Devuelve todos los campos de la asignación (primer usuario) para pre-rellenar el form."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM asignaciones WHERE id = %s LIMIT 1", (aid,))
    row = cur.fetchone()
    cur.execute("SELECT usuario_id FROM asignaciones WHERE id = %s ORDER BY usuario_id", (aid,))
    uids = [r["usuario_id"] for r in cur.fetchall()]
    cur.close(); conn.close()
    if row:
        row = dict(row)
        row["usuario_ids_grupo"] = uids
    return row
    
def _crear_asignacion(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    try:
        uids = data["usuario_ids"]
        if not uids:
            raise ValueError("Debe seleccionar al menos un trabajador.")

        # Obtenemos el próximo id via función SQL de Supabase
        cur.execute("SELECT get_next_asignacion_id() AS nuevo_id")
        row = cur.fetchone()
        nuevo_id = row["nuevo_id"]  # ← acceso por nombre, no por índice
        for uid in uids:
            cur.execute("""
                INSERT INTO asignaciones (id, usuario_id, empresa_id, tarea_id, fecha_meta, estado, peso)
                OVERRIDING SYSTEM VALUE
                VALUES (%s, %s, %s, %s, %s, 'pendiente', %s)
            """, (nuevo_id, uid, data["empresa_id"], data["tarea_id"],
                  data["fecha_meta"], data.get("peso", 1)))

        conn.commit()
    except Exception as ex:
        conn.rollback()
        raise ex
    finally:
        cur.close(); conn.close()

def _actualizar_asignacion_grupo(aid: int, data: dict):
    """
    Actualiza TODAS las filas del grupo (mismo id).
    - Campos comunes se aplican a todas las filas.
    - Si cambia la lista de usuarios: elimina los que ya no están, agrega los nuevos.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        nuevos_uids = set(data["usuario_ids"])

        cur.execute("SELECT usuario_id FROM asignaciones WHERE id = %s", (aid,))
        actuales_uids = {r["usuario_id"] for r in cur.fetchall()}

        eliminar = actuales_uids - nuevos_uids
        agregar  = nuevos_uids  - actuales_uids
        mantener = actuales_uids & nuevos_uids

        # 1. Actualizar filas que permanecen
        if mantener:
            cur.execute("""
                UPDATE asignaciones
                SET empresa_id=%s, tarea_id=%s, fecha_meta=%s, estado=%s, peso=%s
                WHERE id=%s AND usuario_id IN ({})
            """.format(",".join(["%s"] * len(mantener))),
            (data["empresa_id"], data["tarea_id"], data["fecha_meta"],
             data["estado"], data["peso"], aid, *mantener))

        # 2. Eliminar filas que se quitaron
        for uid in eliminar:
            cur.execute(
                "DELETE FROM asignaciones WHERE id=%s AND usuario_id=%s",
                (aid, uid)
            )

        # 3. Insertar nuevos usuarios al grupo con el mismo id existente
        # OVERRIDING SYSTEM VALUE necesario para insertar id explícito
        for uid in agregar:
            cur.execute("""
                INSERT INTO asignaciones (id, usuario_id, empresa_id, tarea_id, fecha_meta, estado, peso)
                OVERRIDING SYSTEM VALUE
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (aid, uid, data["empresa_id"], data["tarea_id"],
                  data["fecha_meta"], data["estado"], data["peso"]))

        conn.commit()
    except Exception as ex:
        conn.rollback()
        raise ex
    finally:
        cur.close(); conn.close()


def _actualizar_estado_grupo(aid: int, nuevo_estado: str):
    """Cambia el estado de TODAS las filas del grupo (mismo id)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE asignaciones SET estado=%s WHERE id=%s",
        (nuevo_estado, aid)
    )
    conn.commit()
    cur.close(); conn.close()


def _eliminar_asignacion_grupo(aid: int):
    """Elimina TODAS las filas del grupo (mismo id)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM asignaciones WHERE id = %s", (aid,))
    conn.commit()
    cur.close(); conn.close()


def _insertar_registro_tarea(asignacion_id, usuario_id, fecha_realizada, rendimiento):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO registros_tareas (asignacion_id, usuario_id, fecha_realizada, rendimiento)
        VALUES (%s, %s, %s, %s)
    """, (asignacion_id, usuario_id, fecha_realizada, rendimiento))
    conn.commit()
    cur.close(); conn.close()


def _calcular_rendimiento(fecha_realizada, fecha_meta):
    if isinstance(fecha_realizada, str):
        fecha_realizada = datetime.strptime(fecha_realizada, "%Y-%m-%d").date()
    if isinstance(fecha_meta, str):
        fecha_meta = datetime.strptime(fecha_meta, "%Y-%m-%d").date()
    if fecha_realizada < fecha_meta:
        return "OPTIMO"
    elif fecha_realizada == fecha_meta:
        return "MEDIO"
    else:
        return "BAJO"
def _insertar_asignacion_bulk(usuario_id, empresa_id, tarea_id, fecha_meta, fecha_realizada, rendimiento):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT get_next_asignacion_id() AS nuevo_id")
        nuevo_id = cur.fetchone()["nuevo_id"]

        cur.execute("""
            INSERT INTO asignaciones (id, usuario_id, empresa_id, tarea_id, fecha_meta, estado, peso)
            VALUES (%s, %s, %s, %s, %s, 'completada', 1)
        """, (nuevo_id, usuario_id, empresa_id, tarea_id, fecha_meta))

        cur.execute("""
            INSERT INTO registros_tareas (asignacion_id, usuario_id, fecha_realizada, rendimiento)
            VALUES (%s, %s, %s, %s)
        """, (nuevo_id, usuario_id, fecha_realizada, rendimiento))

        conn.commit()
        return True, None

    except Exception as ex:
        conn.rollback()
        return False, str(ex)

    finally:
        cur.close()
        conn.close()
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
        fecha_meta = datetime.strptime(fecha_meta, "%Y-%m-%d").date()
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
    """
    Formulario unificado para crear y editar.
    Al crear: multiselect de usuarios.
    Al editar: multiselect también (para poder agregar/quitar usuarios del grupo).
    """
    usuarios = _get_usuarios_activos()
    empresas = _get_empresas_activas()
    tareas   = _get_tareas()

    usr_map  = {f"{u['nom_res']} ({u['alias']})": u["id"] for u in usuarios}
    emp_map  = {f"{e['razon_social']} — {e['ruc']}": e["id"] for e in empresas}
    tar_map  = {f"[{t['nombre_proyecto']}] {t['nombre_tarea']}": t["id"] for t in tareas}

    usr_names = list(usr_map.keys())
    emp_names = list(emp_map.keys())
    tar_names = list(tar_map.keys())

    emp_default = 0
    tar_default = 0

    usr_default_names = []
    if prefill:
        for i, e in enumerate(empresas):
            if e["id"] == prefill.get("empresa_id"):
                emp_default = i
                break
        for i, t in enumerate(tareas):
            if t["id"] == prefill.get("tarea_id"):
                tar_default = i
                break
        grupo_uids = set(prefill.get("usuario_ids_grupo", []))
        usr_default_names = [
            name for name, uid in usr_map.items() if uid in grupo_uids
        ]

    col1, col2 = st.columns(2)
    with col1:
        usr_sel_multi = st.multiselect(
            "Trabajador(es) * — puedes seleccionar más de uno",
            options=usr_names,
            default=usr_default_names,
            key=f"{key_prefix}_usr"
        )
        usuario_ids = [usr_map[n] for n in usr_sel_multi]

        tar_sel = st.selectbox(
            "Tarea *", tar_names, index=tar_default, key=f"{key_prefix}_tar"
        )

    with col2:
        emp_sel = st.selectbox(
            "Empresa *", emp_names, index=emp_default, key=f"{key_prefix}_emp"
        )
        fecha_default = prefill["fecha_meta"] if prefill and prefill.get("fecha_meta") else date.today()
        if isinstance(fecha_default, str):
            fecha_default = datetime.strptime(fecha_default, "%Y-%m-%d").date()
        fecha_meta = st.date_input(
            "Fecha meta *", value=fecha_default,
            format="DD/MM/YYYY", key=f"{key_prefix}_fecha"
        )

    peso_default = int(prefill.get("peso", 1)) if prefill else 1
    if prefill:
        col_peso, col_estado = st.columns(2)
        with col_peso:
            peso = st.number_input(
                "Peso *", min_value=1, max_value=10,
                value=peso_default, step=1, key=f"{key_prefix}_peso"
            )
        with col_estado:
            estado_opts = ["pendiente", "completada", "vencida"]
            estado_idx  = estado_opts.index(prefill.get("estado", "pendiente"))
            estado = st.selectbox(
                "Estado", estado_opts, index=estado_idx, key=f"{key_prefix}_estado"
            )
    else:
        estado = "pendiente"
        peso = st.number_input(
            "Peso * (1=bajo, 10=crítico)", min_value=1, max_value=10,
            value=1, step=1, key=f"{key_prefix}_peso"
        )

    return {
        "usuario_ids":   usuario_ids,
        "usuario_id":    usuario_ids[0] if usuario_ids else None,
        "empresa_id":    emp_map.get(emp_sel),
        "tarea_id":      tar_map.get(tar_sel),
        "fecha_meta":    fecha_meta,
        "estado":        estado,
        "peso":          peso,
        "_trabajadores": usr_sel_multi,
    }


# ================================================================
#  IMPORTACIÓN EXCEL
# ================================================================

def _seccion_importar_excel():
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

    plantilla = pd.DataFrame(columns=[
        "EMPRESA", "PROYECTO", "TAREA", "ENCARGADO",
        "FECHA REALIZADA", "FECHA META", "CANT", "PRIORIDAD"
    ])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        plantilla.to_excel(writer, index=False, sheet_name="Importar")
    buf.seek(0)
    st.download_button(
        "⬇ Descargar plantilla", data=buf,
        file_name="plantilla_asignaciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    archivo = st.file_uploader(
        "Selecciona el archivo Excel", type=["xlsx", "xls"], key="excel_uploader"
    )
    if not archivo:
        return

    try:
        df = pd.read_excel(archivo)
    except Exception as ex:
        st.error(f"No se pudo leer el archivo: {ex}")
        return

    df.columns = [c.strip().upper() for c in df.columns]

    required_cols = {"EMPRESA", "TAREA", "ENCARGADO", "FECHA REALIZADA", "FECHA META", "CANT", "PRIORIDAD"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Faltan columnas: {', '.join(missing)}")
        return

    empresas  = _get_empresas_activas()
    tareas_db = _get_tareas()
    proyectos = _get_proyectos()
    usuarios  = _get_usuarios_activos()

    emp_alias_map      = {e["alias"].strip().upper(): e["id"] for e in empresas}
    usr_id_set         = {int(u["id"]) for u in usuarios}
    tarea_por_numero   = {int(t["id"]): int(t["id"]) for t in tareas_db}
    proyecto_por_tarea = {int(t["id"]): int(t["proyecto_id"]) for t in tareas_db}

    RENDIMIENTOS_VALIDOS = {"BAJO", "MEDIO", "OPTIMO", "URGENTE"}

    errores_import = []
    filas_validas  = []

    for i, row in df.iterrows():
        fila_num = i + 2
        errores_fila = []

        empresa_alias  = str(row.get("EMPRESA", "")).strip().upper()
        tarea_num_raw  = row.get("TAREA")
        encargado_raw  = row.get("ENCARGADO")
        fecha_real_raw = row.get("FECHA REALIZADA")
        fecha_meta_raw = row.get("FECHA META")
        prioridad_raw  = str(row.get("PRIORIDAD", "")).strip().upper()

        empresa_id = emp_alias_map.get(empresa_alias)
        if not empresa_id:
            errores_fila.append(f"Empresa '{empresa_alias}' no encontrada")

        tarea_id = proyecto_id = None
        try:
            tarea_num = int(tarea_num_raw)
            tarea_id  = tarea_por_numero.get(tarea_num)
            if not tarea_id:
                errores_fila.append(f"TAREA {tarea_num} no existe")
            else:
                proyecto_id = proyecto_por_tarea[tarea_id]
        except (TypeError, ValueError):
            errores_fila.append(f"TAREA debe ser número entero (valor: {tarea_num_raw})")

        usuario_id = None
        try:
            uid = int(encargado_raw)
            if uid in usr_id_set:
                usuario_id = uid
            else:
                errores_fila.append(f"Usuario ID {uid} no existe o no está activo")
        except (TypeError, ValueError):
            errores_fila.append(f"ENCARGADO debe ser ID numérico (valor: {encargado_raw})")

        def parse_fecha(val):
            if pd.isna(val) if hasattr(val, '__class__') and val.__class__.__name__ in ('float', 'NaTType') else False:
                return None
            if isinstance(val, date):
                return val
            if hasattr(val, 'date'):
                return val.date()
            try:
                return datetime.strptime(str(val).strip(), "%d/%m/%Y").date()
            except Exception:
                try:
                    return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
                except Exception:
                    return None

        fecha_realizada = parse_fecha(fecha_real_raw)
        fecha_meta      = parse_fecha(fecha_meta_raw)

        if not fecha_realizada:
            errores_fila.append(f"FECHA REALIZADA inválida (valor: {fecha_real_raw})")
        if not fecha_meta:
            errores_fila.append(f"FECHA META inválida (valor: {fecha_meta_raw})")

        rendimiento = prioridad_raw if prioridad_raw in RENDIMIENTOS_VALIDOS else None
        if not rendimiento:
            errores_fila.append(f"PRIORIDAD '{prioridad_raw}' no válida (BAJO/MEDIO/OPTIMO/URGENTE)")

        if errores_fila:
            errores_import.append((fila_num, errores_fila))
        else:
            filas_validas.append({
                "fila":            fila_num,
                "usuario_id":      usuario_id,
                "empresa_id":      empresa_id,
                "tarea_id":        tarea_id,
                "fecha_meta":      fecha_meta,
                "fecha_realizada": fecha_realizada,
                "rendimiento":     rendimiento,
            })

    if errores_import:
        with st.expander(f"⚠ {len(errores_import)} fila(s) con errores (no se importarán)", expanded=True):
            for fila_num, errs in errores_import:
                st.markdown(f"**Fila {fila_num}:** " + " · ".join(errs))

    if not filas_validas:
        st.warning("No hay filas válidas para importar.")
        return

    st.success(f"✅ {len(filas_validas)} fila(s) listas para importar.")

    with st.expander("👁 Vista previa de filas válidas"):
        usr_map_id = {u["id"]: f"{u['nom_res']} ({u['alias']})" for u in usuarios}
        emp_map_id = {e["id"]: e["alias"] for e in empresas}
        tar_map_id = {t["id"]: t["nombre_tarea"] for t in tareas_db}
        preview_rows = [{
            "Fila":        f["fila"],
            "Trabajador":  usr_map_id.get(f["usuario_id"], f["usuario_id"]),
            "Empresa":     emp_map_id.get(f["empresa_id"], f["empresa_id"]),
            "Tarea":       tar_map_id.get(f["tarea_id"], f["tarea_id"]),
            "F. Meta":     f["fecha_meta"],
            "F. Real.":    f["fecha_realizada"],
            "Rendimiento": f["rendimiento"],
        } for f in filas_validas]
        st.dataframe(pd.DataFrame(preview_rows), use_container_width=True)

    if st.button("📥 Confirmar importación", type="primary",
                 use_container_width=True, key="btn_confirmar_import"):
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

    for key, default in [
        ("asig_modo", None),
        ("asig_id_editar", None),
        ("asig_id_eliminar", None),
        ("asig_msg", None),
        ("asig_pagina_actual", 1),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    if st.session_state.asig_msg:
        tipo, texto = st.session_state.asig_msg
        (st.success if tipo == "ok" else st.error)(texto)
        st.session_state.asig_msg = None

    tab_lista, tab_import = st.tabs(["📋 Asignaciones", "📥 Importar Excel"])

    # ── TAB IMPORTAR EXCEL ──────────────────────────────────────
    with tab_import:
        _seccion_importar_excel()

    # ── TAB LISTA DE ASIGNACIONES ───────────────────────────────
    with tab_lista:

        st.markdown("###  Filtros")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_texto = st.text_input(
                "🔎 Buscar por trabajador, empresa o tarea",
                placeholder="Escribe aquí...", label_visibility="collapsed"
            )
        with col_f2:
            filtro_estado = st.selectbox(
                "Estado",
                ["📊 Todos", "⏳ Pendientes", "✅ Completadas", "⚠️ Vencidas"],
                index=0, label_visibility="collapsed"
            )
        with col_f3:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            filtrar_por_fecha = st.checkbox("📅 Por mes/año")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

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
                    index=hoy.month - 1, key="filtro_mes"
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

        # ── FORMULARIO CREAR ────────────────────────────────────
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
                    if not datos["usuario_ids"]: errores.append("Selecciona al menos un trabajador.")
                    if not datos["empresa_id"]:  errores.append("Selecciona una empresa.")
                    if not datos["tarea_id"]:    errores.append("Selecciona una tarea.")
                    if not datos["fecha_meta"]:  errores.append("Ingresa una fecha meta.")

                    if errores:
                        st.session_state.asig_msg = ("error", " | ".join(errores))
                    else:
                        try:
                            _crear_asignacion(datos)
                            n = len(datos["usuario_ids"])
                            msg = (
                                f"✅ Tarea asignada a {n} trabajadores con el mismo ID de asignación."
                                if n > 1
                                else f"✅ Tarea asignada a {datos['_trabajadores'][0]}."
                            )
                            st.session_state.asig_msg  = ("ok", msg)
                            st.session_state.asig_modo = None
                        except Exception as ex:
                            st.session_state.asig_msg = ("error", f"Error al guardar: {ex}")
                    st.rerun()
            with c2:
                if st.button("✖ Cancelar", use_container_width=True, key="btn_cancel_crear_asig"):
                    st.session_state.asig_modo = None
                    st.rerun()

        # ── OBTENER Y FILTRAR ASIGNACIONES ─────────────────────
        solo_completadas = filtrar_por_fecha
        grupos = _get_asignaciones(
            mes=filtro_mes, anio=filtro_anio, solo_completadas=solo_completadas
        )

        estado_map = {
            "📊 Todos":       "Todos",
            "⏳ Pendientes":  "pendiente",
            "✅ Completadas": "completada",
            "⚠️ Vencidas":   "vencida",
        }
        filtro_estado_interno = estado_map.get(filtro_estado, "Todos")

        if filtro_texto:
            q = filtro_texto.lower()
            grupos = [
                g for g in grupos
                if q in g["tarea"].lower()
                or q in g["empresa"].lower()
                or any(q in t["trabajador"].lower() or q in t["alias"].lower()
                       for t in g["trabajadores"])
            ]

        if filtro_estado_interno != "Todos":
            grupos = [g for g in grupos if g["estado"] == filtro_estado_interno]

        total       = len(grupos)
        pendientes  = sum(1 for g in grupos if g["estado"] == "pendiente")
        vencidas    = sum(1 for g in grupos if g["estado"] == "vencida")
        completadas = sum(1 for g in grupos if g["estado"] == "completada")

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

        if not grupos:
            st.info("No hay asignaciones que mostrar.")
            return

        # ── PAGINACIÓN ──────────────────────────────────────────
        REGISTROS_POR_PAGINA = 15
        total_paginas = max(1, (len(grupos) + REGISTROS_POR_PAGINA - 1) // REGISTROS_POR_PAGINA)

        if st.session_state.asig_pagina_actual > total_paginas:
            st.session_state.asig_pagina_actual = total_paginas
        if st.session_state.asig_pagina_actual < 1:
            st.session_state.asig_pagina_actual = 1

        pagina_actual = st.session_state.asig_pagina_actual
        inicio = (pagina_actual - 1) * REGISTROS_POR_PAGINA
        fin    = inicio + REGISTROS_POR_PAGINA
        grupos_pagina = grupos[inicio:fin]

        # Cabecera de tabla
        with st.container(border=False):
            cols_h = st.columns([0.5, 1.2, 1.5, 1, 1, 1.1, 1, 0.9])
            headers = ["ID", "TRABAJADOR(ES)", "EMPRESA", "TAREA", "F. META", "F. REALIZADA", "ESTADO", "ACCIONES"]
            for col, header in zip(cols_h, headers):
                with col:
                    st.markdown(
                        f"<span style='color:rgba(255,255,255,0.4);font-weight:600;"
                        f"font-size:10px;letter-spacing:1px;'>{header}</span>",
                        unsafe_allow_html=True
                    )
        st.divider()

        # ── FILAS ───────────────────────────────────────────────
        for idx, g in enumerate(grupos_pagina):
            aid = g["id"]

            fecha_meta_str = (
                g["fecha_meta"].strftime("%d/%m/%Y")
                if hasattr(g["fecha_meta"], "strftime")
                else str(g["fecha_meta"])
            )
            alerta = _alerta_fecha(g["fecha_meta"], g["estado"])

            trabajadores_html = ""
            for t in g["trabajadores"]:
                fr = t.get("fecha_realizada")
                fr_str = (
                    fr.strftime("%d/%m/%Y") if hasattr(fr, "strftime") else str(fr)
                ) if fr else "—"
                trabajadores_html += (
                    f'<div style="margin-bottom:2px;">'
                    f'<span style="color:white;font-weight:600;font-size:12px;">{t["alias"]}</span>'
                    f'<span style="color:rgba(255,255,255,0.35);font-size:10px;"> · {fr_str}</span>'
                    f'</div>'
                )

            first_fr = g["trabajadores"][0].get("fecha_realizada") if g["trabajadores"] else None
            fecha_realizada_str = (
                first_fr.strftime("%d/%m/%Y") if hasattr(first_fr, "strftime") else str(first_fr)
            ) if first_fr else "—"

            with st.container(border=True):
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(
                    [0.5, 1.2, 1.5, 1, 1, 1.1, 1, 0.9]
                )
                with col1:
                    st.markdown(
                        f'<span style="color:rgba(255,255,255,0.4);font-size:11px;"># {aid}</span>',
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(trabajadores_html, unsafe_allow_html=True)
                with col3:
                    st.markdown(
                        f"<span style='color:rgba(255,255,255,0.7);font-size:12px;'>{g['empresa']}</span>",
                        unsafe_allow_html=True
                    )
                with col4:
                    st.markdown(
                        f"<span style='color:rgba(255,255,255,0.85);font-size:12px;'>{g['tarea']}</span>",
                        unsafe_allow_html=True
                    )
                with col5:
                    st.markdown(
                        f"<span style='color:rgba(255,255,255,0.7);font-size:12px;'>"
                        f"{fecha_meta_str}{alerta}</span>",
                        unsafe_allow_html=True
                    )
                with col6:
                    multi_fr = len(g["trabajadores"]) > 1
                    if multi_fr:
                        st.markdown(
                            f"<span style='color:rgba(255,255,255,0.5);font-size:10px;'>"
                            f"ver trabajadores →</span>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<span style='color:rgba(255,255,255,0.6);font-size:11px;'>"
                            f"{fecha_realizada_str}</span>",
                            unsafe_allow_html=True
                        )
                with col7:
                    st.markdown(_badge_estado(g["estado"]), unsafe_allow_html=True)
                with col8:
                    ba1, ba2 = st.columns(2, gap="small")
                    with ba1:
                        if st.button("🖍", key=f"edit_asig_{aid}_{idx}", help="Editar", use_container_width=True):
                            st.session_state.asig_modo      = "editar"
                            st.session_state.asig_id_editar = aid
                            st.rerun()
                    with ba2:
                        if st.button("🗑️", key=f"del_asig_{aid}_{idx}", help="Eliminar", use_container_width=True):
                            st.session_state.asig_id_eliminar = aid
                            st.rerun()

            # ── Formulario editar inline ────────────────────────
            if st.session_state.asig_modo == "editar" and st.session_state.asig_id_editar == aid:
                prefill = _get_asignacion_grupo_by_id(aid)
                n_trabajadores = len(g["trabajadores"])
                aviso_grupo = (
                    f'<span style="color:#f6c27d;font-size:11px;">'
                    f'⚠ Esta asignación tiene <b>{n_trabajadores} trabajadores</b>. '
                    f'Los cambios de estado y campos comunes se aplicarán a todos.</span>'
                ) if n_trabajadores > 1 else ""

                st.markdown(f"""
                <div style="background:rgba(133,183,235,0.06);border:1px solid rgba(133,183,235,0.2);
                            border-radius:16px;padding:20px 24px;margin:8px 0 16px;">
                    <h4 style="color:#85B7EB;margin:0 0 8px;">Editando asignación #{aid}</h4>
                    {aviso_grupo}
                </div>
                """, unsafe_allow_html=True)

                datos = _form_asignacion(prefill=prefill, key_prefix=f"edit_{aid}_{idx}")

                e1, e2 = st.columns(2)
                with e1:
                    if st.button("💾 Actualizar", use_container_width=True,
                                 key=f"btn_upd_asig_{aid}_{idx}"):
                        errores = []
                        if not datos["usuario_ids"]: errores.append("Selecciona al menos un trabajador.")
                        if not datos["empresa_id"]:  errores.append("Selecciona una empresa.")
                        if not datos["tarea_id"]:    errores.append("Selecciona una tarea.")

                        if errores:
                            st.session_state.asig_msg = ("error", " | ".join(errores))
                        else:
                            try:
                                _actualizar_asignacion_grupo(aid, datos)
                                st.session_state.asig_msg       = ("ok", f"✅ Asignación #{aid} actualizada.")
                                st.session_state.asig_modo      = None
                                st.session_state.asig_id_editar = None
                                st.session_state.asig_pagina_actual = 1
                            except Exception as ex:
                                st.session_state.asig_msg = ("error", f"Error: {ex}")
                        st.rerun()
                with e2:
                    if st.button("✖ Cancelar", use_container_width=True,
                                 key=f"btn_cancel_edit_asig_{aid}_{idx}"):
                        st.session_state.asig_modo      = None
                        st.session_state.asig_id_editar = None
                        st.rerun()

            # ── Confirmación eliminar ───────────────────────────
            if st.session_state.asig_id_eliminar == aid:
                n_trabajadores = len(g["trabajadores"])
                detalle = (
                    f" (afecta a {n_trabajadores} trabajadores del grupo)"
                    if n_trabajadores > 1 else ""
                )
                st.warning(
                    f"¿Eliminar la asignación **#{aid}** — {g['tarea']} / {g['empresa']}?{detalle}"
                )
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("🗑️ Confirmar", use_container_width=True,
                                 key=f"confirm_del_asig_{aid}_{idx}", type="primary"):
                        try:
                            _eliminar_asignacion_grupo(aid)
                            st.session_state.asig_msg         = ("ok", f"✅ Asignación #{aid} eliminada.")
                            st.session_state.asig_id_eliminar = None
                            st.session_state.asig_pagina_actual = 1
                        except Exception as ex:
                            st.session_state.asig_msg = ("error", f"No se puede eliminar: {ex}")
                        st.rerun()
                with d2:
                    if st.button("✖ Cancelar", use_container_width=True,
                                 key=f"cancel_del_asig_{aid}_{idx}"):
                        st.session_state.asig_id_eliminar = None
                        st.rerun()

        # ── Paginación ──────────────────────────────────────────
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
        with col_pag1:
            if st.button("← Anterior", use_container_width=True, disabled=(pagina_actual == 1)):
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
            if st.button("Siguiente →", use_container_width=True, disabled=(pagina_actual == total_paginas)):
                st.session_state.asig_pagina_actual = pagina_actual + 1
                st.rerun()