import streamlit as st
from config.db import get_connection

# ================================================================
#  REPOSITORIO
# ================================================================

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


def _get_tarea_by_id(tid: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id = %s", (tid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def _crear_tarea(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tareas (nombre_tarea, proyecto_id)
        VALUES (%s, %s)
    """, (data["nombre_tarea"], data["proyecto_id"]))
    conn.commit()
    cur.close(); conn.close()


def _actualizar_tarea(tid: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tareas SET nombre_tarea=%s, proyecto_id=%s
        WHERE id=%s
    """, (data["nombre_tarea"], data["proyecto_id"], tid))
    conn.commit()
    cur.close(); conn.close()


def _eliminar_tarea(tid: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tareas WHERE id = %s", (tid,))
    conn.commit()
    cur.close(); conn.close()


def _tarea_existe(nombre_tarea: str, proyecto_id: int, excluir_id: int = None):
    conn = get_connection()
    cur = conn.cursor()
    if excluir_id:
        cur.execute(
            "SELECT id FROM tareas WHERE nombre_tarea=%s AND proyecto_id=%s AND id!=%s",
            (nombre_tarea, proyecto_id, excluir_id)
        )
    else:
        cur.execute(
            "SELECT id FROM tareas WHERE nombre_tarea=%s AND proyecto_id=%s",
            (nombre_tarea, proyecto_id)
        )
    existe = cur.fetchone() is not None
    cur.close(); conn.close()
    return existe


# ================================================================
#  HELPERS UI
# ================================================================

def _badge_proyecto(nombre: str) -> str:
    return (
        f'<span style="background:rgba(133,183,235,0.12);color:#85B7EB;'
        f'padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700;">'
        f'{nombre}</span>'
    )


def _form_tarea(prefill: dict = None, key_prefix: str = "new"):
    proyectos = _get_proyectos()
    proy_map   = {p["nombre_proyecto"]: p["id"] for p in proyectos}
    proy_names = list(proy_map.keys())

    default_proy_idx = 0
    if prefill and prefill.get("proyecto_id"):
        for i, p in enumerate(proyectos):
            if p["id"] == prefill["proyecto_id"]:
                default_proy_idx = i
                break

    col1, col2 = st.columns(2)
    with col1:
        nombre_tarea = st.text_input(
            "Nombre de la tarea *",
            value=prefill.get("nombre_tarea", "") if prefill else "",
            key=f"{key_prefix}_nombre"
        )
    with col2:
        proy_sel = st.selectbox(
            "Proyecto *",
            proy_names,
            index=default_proy_idx,
            key=f"{key_prefix}_proy"
        )

    return {
        "nombre_tarea": nombre_tarea.strip().upper(),
        "proyecto_id":  proy_map.get(proy_sel),
    }


# ================================================================
#  VISTA PRINCIPAL
# ================================================================

def admin_tareas():

    st.markdown("""
    <div style="margin-bottom:24px;">
        <h2 style="color:#f6c27d;font-size:22px;font-weight:800;margin:0;">Gestión de Tareas</h2>
        <p style="color:rgba(255,255,255,0.5);font-size:13px;margin-top:4px;">
            Administra las tareas asociadas a cada proyecto
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Inicializar estados ──────────────────────────────────────
    for key in ["tar_modo", "tar_id_editar", "tar_id_eliminar", "tar_msg"]:
        if key not in st.session_state:
            st.session_state[key] = None

    # ── Mensaje de feedback ──────────────────────────────────────
    if st.session_state.tar_msg:
        tipo, texto = st.session_state.tar_msg
        (st.success if tipo == "ok" else st.error)(texto)
        st.session_state.tar_msg = None

    # ── Barra superior ───────────────────────────────────────────
    col_busq, col_btn = st.columns([3, 1])
    with col_busq:
        busqueda = st.text_input(
            "🔍 Buscar por nombre de tarea o proyecto",
            placeholder="Escribe para filtrar...",
            label_visibility="collapsed"
        )
    with col_btn:
        if st.button("➕ Nueva tarea", use_container_width=True):
            st.session_state.tar_modo     = "crear"
            st.session_state.tar_id_editar = None

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ================================================================
    #  FORMULARIO CREAR
    # ================================================================
    if st.session_state.tar_modo == "crear":
        st.markdown("""
        <div style="background:rgba(246,194,125,0.06);border:1px solid rgba(246,194,125,0.2);
                    border-radius:16px;padding:20px 24px;margin-bottom:20px;">
            <h4 style="color:#f6c27d;margin:0 0 16px;">Nueva tarea</h4>
        </div>
        """, unsafe_allow_html=True)

        datos = _form_tarea(key_prefix="crear")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Guardar", use_container_width=True, key="btn_crear_tar"):
                errores = []
                if not datos["nombre_tarea"]: errores.append("Nombre de tarea requerido.")
                if not datos["proyecto_id"]:  errores.append("Proyecto requerido.")
                if datos["nombre_tarea"] and datos["proyecto_id"] and \
                   _tarea_existe(datos["nombre_tarea"], datos["proyecto_id"]):
                    errores.append("Ya existe una tarea con ese nombre en el mismo proyecto.")

                if errores:
                    st.session_state.tar_msg = ("error", " | ".join(errores))
                else:
                    try:
                        _crear_tarea(datos)
                        st.session_state.tar_msg  = ("ok", f"✅ Tarea '{datos['nombre_tarea']}' creada.")
                        st.session_state.tar_modo = None
                    except Exception as e:
                        st.session_state.tar_msg = ("error", f"Error al crear: {e}")
                st.rerun()
        with c2:
            if st.button("✖ Cancelar", use_container_width=True, key="btn_cancel_crear_tar"):
                st.session_state.tar_modo = None
                st.rerun()

    # ================================================================
    #  TABLA DE TAREAS
    # ================================================================
    tareas = _get_tareas()

    if busqueda:
        q = busqueda.lower()
        tareas = [t for t in tareas if
                  q in t["nombre_tarea"].lower() or
                  q in t["nombre_proyecto"].lower()]

    if not tareas:
        st.info("No se encontraron tareas.")
        return

    st.markdown("### Lista de Tareas")

    # Encabezado de la tabla
    with st.container(border=False):
        col1, col2, col3, col4 = st.columns([0.5, 2.5, 2, 1])
        for col, header in zip(
            [col1, col2, col3, col4],
            ["ID", "NOMBRE TAREA", "PROYECTO", "ACCIONES"]
        ):
            with col:
                st.markdown(
                    f"<span style='color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;'>{header}</span>",
                    unsafe_allow_html=True
                )

    st.divider()

    for t in tareas:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([0.5, 2.5, 2, 1])

            with col1:
                st.markdown(
                    f"<span style='color:rgba(255,255,255,0.4);font-size:11px;'>#{t['id']}</span>",
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f"<span style='color:white;font-weight:600;font-size:14px;'>{t['nombre_tarea']}</span>",
                    unsafe_allow_html=True
                )
            with col3:
                st.markdown(_badge_proyecto(t["nombre_proyecto"]), unsafe_allow_html=True)
            with col4:
                col_edit, col_del = st.columns(2, gap="small")
                with col_edit:
                    if st.button("🖍", key=f"edit_tar_{t['id']}", help="Editar", use_container_width=True):
                        st.session_state.tar_modo      = "editar"
                        st.session_state.tar_id_editar = t["id"]
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_tar_{t['id']}", help="Eliminar", use_container_width=True):
                        st.session_state.tar_id_eliminar = t["id"]
                        st.rerun()

        # ── Formulario editar inline ─────────────────────────────
        if st.session_state.tar_modo == "editar" and st.session_state.tar_id_editar == t["id"]:
            prefill = _get_tarea_by_id(t["id"])
            st.markdown(f"""
            <div style="background:rgba(133,183,235,0.06);border:1px solid rgba(133,183,235,0.2);
                        border-radius:16px;padding:20px 24px;margin:8px 0 16px;">
                <h4 style="color:#85B7EB;margin:0 0 16px;">Editando: {t['nombre_tarea']}</h4>
            </div>
            """, unsafe_allow_html=True)

            datos = _form_tarea(prefill=prefill, key_prefix=f"edit_tar_{t['id']}")

            e1, e2 = st.columns(2)
            with e1:
                if st.button("💾 Actualizar", use_container_width=True, key=f"btn_upd_tar_{t['id']}"):
                    errores = []
                    if not datos["nombre_tarea"]: errores.append("Nombre de tarea requerido.")
                    if not datos["proyecto_id"]:  errores.append("Proyecto requerido.")
                    if datos["nombre_tarea"] and datos["proyecto_id"] and \
                       _tarea_existe(datos["nombre_tarea"], datos["proyecto_id"], excluir_id=t["id"]):
                        errores.append("Ya existe una tarea con ese nombre en el mismo proyecto.")

                    if errores:
                        st.session_state.tar_msg = ("error", " | ".join(errores))
                    else:
                        try:
                            _actualizar_tarea(t["id"], datos)
                            st.session_state.tar_msg       = ("ok", f"✅ Tarea actualizada.")
                            st.session_state.tar_modo      = None
                            st.session_state.tar_id_editar = None
                        except Exception as ex:
                            st.session_state.tar_msg = ("error", f"Error al actualizar: {ex}")
                    st.rerun()
            with e2:
                if st.button("✖ Cancelar", use_container_width=True, key=f"btn_cancel_edit_tar_{t['id']}"):
                    st.session_state.tar_modo      = None
                    st.session_state.tar_id_editar = None
                    st.rerun()

        # ── Confirmación eliminar ────────────────────────────────
        if st.session_state.tar_id_eliminar == t["id"]:
            st.warning(f"¿Eliminar la tarea **{t['nombre_tarea']}**? Esta acción no se puede deshacer.")
            d1, d2 = st.columns(2)
            with d1:
                if st.button("🗑️ Confirmar", use_container_width=True,
                             key=f"confirm_del_tar_{t['id']}", type="primary"):
                    try:
                        _eliminar_tarea(t["id"])
                        st.session_state.tar_msg         = ("ok", "✅ Tarea eliminada.")
                        st.session_state.tar_id_eliminar = None
                    except Exception as ex:
                        st.session_state.tar_msg = ("error", f"No se puede eliminar: {ex}")
                    st.rerun()
            with d2:
                if st.button("✖ Cancelar", use_container_width=True, key=f"cancel_del_tar_{t['id']}"):
                    st.session_state.tar_id_eliminar = None
                    st.rerun()