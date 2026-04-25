import streamlit as st
from config.db import get_connection
from datetime import date


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
        SELECT id, razon_social, ruc
        FROM empresas
        WHERE estado_contrato = 'Activo'
        ORDER BY razon_social
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_tareas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_tarea FROM tareas ORDER BY nombre_tarea")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_asignaciones():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            a.id,
            u.nom_res       AS trabajador,
            u.alias         AS alias,
            e.razon_social  AS empresa,
            t.nombre_tarea  AS tarea,
            a.fecha_meta,
            a.estado,
            a.peso,
            a.fecha_creacion
        FROM asignaciones a
        JOIN usuarios u ON a.usuario_id = u.id
        JOIN empresas e ON a.empresa_id = e.id
        JOIN tareas   t ON a.tarea_id   = t.id
        ORDER BY a.fecha_meta ASC, a.id DESC
    """)
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
        INSERT INTO asignaciones (usuario_id, empresa_id, tarea_id, fecha_meta, estado, peso)
        VALUES (%s, %s, %s, %s, 'pendiente', %s)
    """, (data["usuario_id"], data["empresa_id"], data["tarea_id"],
          data["fecha_meta"], data["peso"]))
    conn.commit()
    cur.close(); conn.close()


def _actualizar_asignacion(aid: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE asignaciones
        SET usuario_id=%s, empresa_id=%s, tarea_id=%s, fecha_meta=%s, estado=%s, peso=%s
        WHERE id=%s
    """, (data["usuario_id"], data["empresa_id"], data["tarea_id"],
          data["fecha_meta"], data["estado"], data["peso"], aid))
    conn.commit()
    cur.close(); conn.close()


def _eliminar_asignacion(aid: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM asignaciones WHERE id = %s", (aid,))
    conn.commit()
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


def _badge_peso(peso: int) -> str:
    if peso >= 8:
        bg, color = "rgba(240,149,149,0.15)", "#F09595"
    elif peso >= 4:
        bg, color = "rgba(246,194,125,0.15)", "#f6c27d"
    else:
        bg, color = "rgba(93,202,165,0.15)", "#5DCAA5"
    return f'<span style="background:{bg};color:{color};padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;">P:{peso}</span>'


def _alerta_fecha(fecha_meta) -> str:
    if not fecha_meta:
        return ""
    hoy = date.today()
    if isinstance(fecha_meta, str):
        from datetime import datetime
        fecha_meta = datetime.strptime(fecha_meta, "%Y-%m-%d").date()
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
    emp_map = {f"{e['razon_social']} — {e['ruc']}":  e["id"] for e in empresas}
    tar_map = {t["nombre_tarea"]: t["id"] for t in tareas}

    usr_names = list(usr_map.keys())
    emp_names = list(emp_map.keys())
    tar_names = list(tar_map.keys())

    usr_default = 0
    emp_default = 0
    tar_default = 0

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

    # ── Fila inferior: peso + estado (en edición) ────────────────
    peso_default = prefill.get("peso", 1) if prefill else 1

    if prefill:
        col_peso, col_estado = st.columns(2)
        with col_peso:
            peso = st.number_input(
                "Peso * " ,
                min_value=1, max_value=10,
                value=int(peso_default),
                step=1,
                key=f"{key_prefix}_peso"
            )
        with col_estado:
            estado = st.selectbox(
                "Estado",
                ["pendiente", "completada", "vencida"],
                index=["pendiente", "completada", "vencida"].index(
                    prefill.get("estado", "pendiente")),
                key=f"{key_prefix}_estado"
            )
    else:
        estado = "pendiente"
        peso = st.number_input(
            "Peso * (1 = bajo, 10 = crítico)",
            min_value=1, max_value=10,
            value=1,
            step=1,
            key=f"{key_prefix}_peso"
        )

    return {
        "usuario_id": usr_map.get(usr_sel),
        "empresa_id": emp_map.get(emp_sel),
        "tarea_id":   tar_map.get(tar_sel),
        "fecha_meta": fecha_meta,
        "estado":     estado,
        "peso":       peso,
        # para el mensaje de confirmación
        "_trabajador": usr_sel,
        "_tarea":      tar_sel,
    }


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
    for key in ["asig_modo", "asig_id_editar", "asig_id_eliminar", "asig_msg"]:
        if key not in st.session_state:
            st.session_state[key] = None

    # ── Mensaje de feedback ──────────────────────────────────────
    if st.session_state.asig_msg:
        tipo, texto = st.session_state.asig_msg
        (st.success if tipo == "ok" else st.error)(texto)
        st.session_state.asig_msg = None

    # ── Filtros + botón nuevo ────────────────────────────────────
    col_f1, col_f2, col_btn = st.columns([2, 2, 1])
    with col_f1:
        filtro_texto = st.text_input("🔍 Buscar tarea o empresa",
                                    placeholder="Escribe para filtrar...",
                                    label_visibility="collapsed")
    with col_f2:
        filtro_estado = st.selectbox("Estado", ["Todos", "pendiente", "completada", "vencida"],
                                    label_visibility="collapsed")
    with col_btn:
        if st.button("➕ Nueva asignación", use_container_width=True):
            st.session_state.asig_modo      = "crear"
            st.session_state.asig_id_editar = None

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

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
    asignaciones = _get_asignaciones()

    # Filtros
    if filtro_texto:
        q = filtro_texto.lower()
        asignaciones = [a for a in asignaciones if
                        q in a["tarea"].lower() or
                        q in a["empresa"].lower() or
                        q in a["trabajador"].lower()]

    if filtro_estado != "Todos":
        asignaciones = [a for a in asignaciones if a["estado"] == filtro_estado]

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

    # Cabecera tabla
    st.markdown("""
    <div style="display:grid;grid-template-columns:1.5fr 2fr 1.8fr 1fr 1fr 80px 90px;
                gap:8px;padding:8px 16px;
                color:rgba(255,255,255,0.4);font-size:11px;
                letter-spacing:1px;text-transform:uppercase;
                border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:4px;">
        <span>Trabajador</span>
        <span>Empresa</span>
        <span>Tarea</span>
        <span>Fecha meta</span>
        <span>Estado</span>
        <span>Peso</span>
        <span></span>
    </div>
    """, unsafe_allow_html=True)

    for a in asignaciones:
        fecha_str = a["fecha_meta"].strftime("%d/%m/%Y") if hasattr(a["fecha_meta"], "strftime") else str(a["fecha_meta"])
        alerta    = _alerta_fecha(a["fecha_meta"])
        peso_val  = a.get("peso", 1) or 1

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1.5fr 2fr 1.8fr 1fr 1fr 80px 90px;
                    gap:8px;align-items:center;padding:12px 16px;
                    background:rgba(255,255,255,0.03);border-radius:12px;
                    border:1px solid rgba(255,255,255,0.05);margin-bottom:6px;">
            <div>
                <span style="color:white;font-weight:600;font-size:13px;">{a['alias']}</span>
                <span style="color:rgba(255,255,255,0.4);font-size:11px;display:block;">{a['trabajador']}</span>
            </div>
            <span style="color:rgba(255,255,255,0.7);font-size:12px;">{a['empresa']}</span>
            <span style="color:rgba(255,255,255,0.85);font-size:12px;">{a['tarea']}</span>
            <span style="color:rgba(255,255,255,0.7);font-size:12px;">{fecha_str}{alerta}</span>
            <span>{_badge_estado(a['estado'])}</span>
            <span>{_badge_peso(peso_val)}</span>
            <span></span>
        </div>
        """, unsafe_allow_html=True)

        # Botones acción
        _, _, _, _, _, _, col_acc = st.columns([1.5, 2, 1.8, 1, 1, 0.8, 0.9])
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

        # ── Formulario editar inline ─────────────────────────────
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
                        except Exception as ex:
                            st.session_state.asig_msg = ("error", f"Error: {ex}")
                    st.rerun()
            with e2:
                if st.button("✖ Cancelar", use_container_width=True, key=f"btn_cancel_edit_asig_{a['id']}"):
                    st.session_state.asig_modo      = None
                    st.session_state.asig_id_editar = None
                    st.rerun()

        # ── Confirmación eliminar ────────────────────────────────
        if st.session_state.asig_id_eliminar == a["id"]:
            st.warning(f"¿Eliminar la asignación de **{a['tarea']}** para {a['alias']}?")
            d1, d2 = st.columns(2)
            with d1:
                if st.button(" Confirmar", use_container_width=True,
                             key=f"confirm_del_asig_{a['id']}", type="primary"):
                    try:
                        _eliminar_asignacion(a["id"])
                        st.session_state.asig_msg         = ("ok", "✅ Asignación eliminada.")
                        st.session_state.asig_id_eliminar = None
                    except Exception as ex:
                        st.session_state.asig_msg = ("error", f"No se puede eliminar: {ex}")
                    st.rerun()
            with d2:
                if st.button("✖ Cancelar", use_container_width=True, key=f"cancel_del_asig_{a['id']}"):
                    st.session_state.asig_id_eliminar = None
                    st.rerun()