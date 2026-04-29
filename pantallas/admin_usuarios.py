import streamlit as st
from config.db import get_connection


# ================================================================
#  REPOSITORIO — solo habla con la BD
# ================================================================

def _get_areas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_area FROM areas ORDER BY nombre_area")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_subareas(area_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, nombre_subarea FROM subareas WHERE area_id = %s ORDER BY nombre_subarea",
        (area_id,)
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_usuarios():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.nom_res, u.alias, u.usuario,
               u.rol, u.estado,
               a.nombre_area,
               s.id        AS subarea_id,
               s.nombre_subarea,
               s.area_id,
               u.fecha_creacion
        FROM usuarios u
        LEFT JOIN subareas s ON u.subarea_id = s.id
        LEFT JOIN areas    a ON s.area_id    = a.id
        ORDER BY u.id
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_usuario_by_id(uid: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.*, s.area_id
        FROM usuarios u
        LEFT JOIN subareas s ON u.subarea_id = s.id
        WHERE u.id = %s
    """, (uid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def _crear_usuario(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO usuarios (nom_res, alias, usuario, password, subarea_id, rol, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        data["nom_res"], data["alias"], data["usuario"],
        data["password"],
        data["subarea_id"],
        data["rol"], data["estado"]
    ))
    conn.commit()
    cur.close(); conn.close()


def _actualizar_usuario(uid: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    if data.get("nueva_password"):
        cur.execute("""
            UPDATE usuarios
            SET nom_res=%s, alias=%s, usuario=%s, password=%s,
                subarea_id=%s, rol=%s, estado=%s
            WHERE id=%s
        """, (
            data["nom_res"], data["alias"], data["usuario"],
            data["nueva_password"],
            data["subarea_id"],
            data["rol"], data["estado"], uid
        ))
    else:
        cur.execute("""
            UPDATE usuarios
            SET nom_res=%s, alias=%s, usuario=%s,
                subarea_id=%s, rol=%s, estado=%s
            WHERE id=%s
        """, (
            data["nom_res"], data["alias"], data["usuario"],
            data["subarea_id"],
            data["rol"], data["estado"], uid
        ))
    conn.commit()
    cur.close(); conn.close()


def _eliminar_usuario(uid: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
    conn.commit()
    cur.close(); conn.close()


def _usuario_existe(usuario: str, excluir_id: int = None):
    conn = get_connection()
    cur = conn.cursor()
    if excluir_id:
        cur.execute(
            "SELECT id FROM usuarios WHERE usuario = %s AND id != %s",
            (usuario, excluir_id)
        )
    else:
        cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (usuario,))
    existe = cur.fetchone() is not None
    cur.close(); conn.close()
    return existe


# ================================================================
#  HELPERS UI
# ================================================================

def _badge_rol(rol: str) -> str:
    color = "#f6c27d" if rol == "admin" else "#85B7EB"
    return (
        f'<span style="background:rgba(255,255,255,0.08);color:{color};'
        f'padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700;">'
        f'{rol.upper()}</span>'
    )


def _badge_estado(estado: str) -> str:
    if estado == "activo":
        return (
            '<span style="background:rgba(93,202,165,0.15);color:#5DCAA5;'
            'padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700;">ACTIVO</span>'
        )
    return (
        '<span style="background:rgba(240,149,149,0.15);color:#F09595;'
        'padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700;">INACTIVO</span>'
    )


def _form_usuario(prefill: dict = None, key_prefix: str = "nuevo"):
    """
    Formulario reutilizable para crear y editar.
    La tabla usuarios NO tiene area_id; el área se deduce a través de subareas.
    Flujo: seleccionar Área → filtra Subáreas → guarda solo subarea_id.
    """
    areas = _get_areas()
    area_map   = {a["nombre_area"]: a["id"] for a in areas}
    area_names = list(area_map.keys())

    # Determinar área preseleccionada (viene de la JOIN en _get_usuario_by_id)
    default_area_name = None
    if prefill and prefill.get("area_id"):
        for a in areas:
            if a["id"] == prefill["area_id"]:
                default_area_name = a["nombre_area"]
                break

    area_options = ["— Sin área —"] + area_names
    default_area_idx = (
        area_options.index(default_area_name)
        if default_area_name and default_area_name in area_options
        else 0
    )

    col1, col2 = st.columns(2)

    with col1:
        nom_res = st.text_input(
            "Nombre completo",
            value=prefill.get("nom_res", "") if prefill else "",
            key=f"{key_prefix}_nom"
        )
        usuario = st.text_input(
            "Usuario (login)",
            value=prefill.get("usuario", "") if prefill else "",
            key=f"{key_prefix}_usr"
        )
        area_sel = st.selectbox(
            "Área",
            area_options,
            index=default_area_idx,
            key=f"{key_prefix}_area"
        )

    with col2:
        alias = st.text_input(
            "Alias",
            value=prefill.get("alias", "") if prefill else "",
            key=f"{key_prefix}_alias"
        )
        rol = st.selectbox(
            "Rol", ["trabajador", "admin"],
            index=0 if not prefill else (0 if prefill.get("rol") == "trabajador" else 1),
            key=f"{key_prefix}_rol"
        )
        estado = st.selectbox(
            "Estado", ["activo", "inactivo"],
            index=0 if not prefill else (0 if prefill.get("estado") == "activo" else 1),
            key=f"{key_prefix}_estado"
        )

    # Subárea — depende del área seleccionada
    subarea_id = None
    if area_sel != "— Sin área —":
        area_id_sel = area_map[area_sel]
        subareas = _get_subareas(area_id_sel)
        if subareas:
            sub_map   = {s["nombre_subarea"]: s["id"] for s in subareas}
            sub_names = list(sub_map.keys())

            # Preseleccionar subárea si estamos editando
            default_sub_idx = 0
            if prefill and prefill.get("subarea_id"):
                sub_ids = [s["id"] for s in subareas]
                if prefill["subarea_id"] in sub_ids:
                    default_sub_idx = sub_ids.index(prefill["subarea_id"]) + 1  # +1 por "— Sin subárea —"

            sub_options = ["— Sin subárea —"] + sub_names
            sub_sel = st.selectbox(
                "Subárea",
                sub_options,
                index=default_sub_idx,
                key=f"{key_prefix}_sub"
            )
            if sub_sel != "— Sin subárea —":
                subarea_id = sub_map[sub_sel]
        else:
            st.caption("Esta área no tiene subáreas registradas.")
    else:
        st.empty()  # Mantiene el layout consistente

    # Contraseña
    if prefill:
        nueva_pw = st.text_input(
            "Nueva contraseña (dejar vacío para no cambiar)",
            type="password", key=f"{key_prefix}_pw"
        )
    else:
        nueva_pw = st.text_input(
            "Contraseña *", type="password", key=f"{key_prefix}_pw"
        )

    return {
        "nom_res":        nom_res.strip(),
        "alias":          alias.strip().upper(),
        "usuario":        usuario.strip(),
        "nueva_password": nueva_pw,
        "password":       nueva_pw,
        "subarea_id":     subarea_id,   # ← único campo que va a la BD
        "rol":            rol,
        "estado":         estado,
    }


# ================================================================
#  VISTA PRINCIPAL
# ================================================================

def admin_usuarios():

    st.markdown("""
    <div style="margin-bottom:24px;">
        <h2 style="color:#f6c27d;font-size:22px;font-weight:800;margin:0;">Gestión de Usuarios</h2>
        <p style="color:rgba(255,255,255,0.5);font-size:13px;margin-top:4px;">
            Crea, edita y administra las cuentas del sistema
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Inicializar estados ──────────────────────────────────────
    for key in ["modo_crud", "uid_editar", "uid_eliminar", "crud_msg"]:
        if key not in st.session_state:
            st.session_state[key] = None

    # ── Mensaje de feedback ──────────────────────────────────────
    if st.session_state.crud_msg:
        tipo, texto = st.session_state.crud_msg
        (st.success if tipo == "ok" else st.error)(texto)
        st.session_state.crud_msg = None

    # ── Barra superior ───────────────────────────────────────────
    col_busq, col_btn = st.columns([3, 1])
    with col_busq:
        busqueda = st.text_input(
            "🔍 Buscar por nombre, alias o usuario",
            placeholder="Escribe para filtrar...",
            label_visibility="collapsed"
        )
    with col_btn:
        if st.button("➕ Nuevo usuario", use_container_width=True):
            st.session_state.modo_crud  = "crear"
            st.session_state.uid_editar = None

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ================================================================
    #  FORMULARIO CREAR
    # ================================================================
    if st.session_state.modo_crud == "crear":
        with st.container():
            st.markdown("""
            <div style="background:rgba(246,194,125,0.06);border:1px solid rgba(246,194,125,0.2);
                        border-radius:16px;padding:20px 24px;margin-bottom:20px;">
                <h4 style="color:#f6c27d;margin:0 0 16px;">Nuevo usuario</h4>
            """, unsafe_allow_html=True)

            datos = _form_usuario(key_prefix="crear")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Guardar", use_container_width=True, key="btn_guardar_crear"):
                    errores = []
                    if not datos["nom_res"]:  errores.append("Nombre completo requerido.")
                    if not datos["alias"]:    errores.append("Alias requerido.")
                    if not datos["usuario"]:  errores.append("Usuario requerido.")
                    if not datos["password"]: errores.append("Contraseña requerida.")
                    if _usuario_existe(datos["usuario"]):
                        errores.append(f"El usuario '{datos['usuario']}' ya existe.")

                    if errores:
                        st.session_state.crud_msg = ("error", " | ".join(errores))
                    else:
                        try:
                            _crear_usuario(datos)
                            st.session_state.crud_msg  = ("ok", f"✅ Usuario '{datos['alias']}' creado correctamente.")
                            st.session_state.modo_crud = None
                        except Exception as e:
                            st.session_state.crud_msg = ("error", f"Error al crear: {e}")
                    st.rerun()

            with c2:
                if st.button("✖ Cancelar", use_container_width=True, key="btn_cancel_crear"):
                    st.session_state.modo_crud = None
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ================================================================
    #  TABLA DE USUARIOS
    # ================================================================
    usuarios = _get_usuarios()

    # Filtro de búsqueda
    if busqueda:
        q = busqueda.lower()
        usuarios = [u for u in usuarios if
                    q in u["nom_res"].lower() or
                    q in u["alias"].lower() or
                    q in u["usuario"].lower()]

    if not usuarios:
        st.info("No se encontraron usuarios.")
        return

    # Cabecera tabla
    with st.container(border=False):
        col1, col2, col3, col4, col5, col6 = st.columns([2.5, 1, 1.5, 1, 1, 0.8])
        headers = ["NOMBRE / ALIAS", "USUARIO", "ÁREA · SUBÁREA", "ROL", "ESTADO", "ACCIONES"]
        for col, header in zip([col1, col2, col3, col4, col5, col6], headers):
            with col:
                st.markdown(
                    f"<span style='color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;'>{header}</span>",
                    unsafe_allow_html=True
                )

    st.divider()

    for u in usuarios:
        area_info = u.get("nombre_area") or "—"
        sub_info  = u.get("nombre_subarea") or ""
        area_str  = area_info + (f" · {sub_info}" if sub_info else "")

        with st.container(border=True):
            col1, col2, col3, col4, col5, col6 = st.columns([2.5, 1, 1.5, 1, 1, 0.8])

            with col1:
                st.markdown(f"""
                <div>
                    <span style="color:white;font-weight:600;font-size:14px;">{u['nom_res']}</span>
                    <br><span style="color:rgba(255,255,255,0.35);font-size:11px;">{u['alias']}</span>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.caption(u['usuario'])

            with col3:
                st.caption(area_str)

            with col4:
                st.markdown(_badge_rol(u['rol']), unsafe_allow_html=True)

            with col5:
                st.markdown(_badge_estado(u['estado']), unsafe_allow_html=True)

            with col6:
                bc1, bc2 = st.columns(2, gap="small")
                with bc1:
                    if st.button("🖍", key=f"edit_{u['id']}", help="Editar", use_container_width=True):
                        st.session_state.modo_crud  = "editar"
                        st.session_state.uid_editar = u["id"]
                        st.rerun()
                with bc2:
                    if st.button("🗑️", key=f"del_{u['id']}", help="Eliminar", use_container_width=True):
                        st.session_state.uid_eliminar = u["id"]
                        st.rerun()

        # ── Formulario editar (inline bajo la fila) ──────────────
        if st.session_state.modo_crud == "editar" and st.session_state.uid_editar == u["id"]:
            prefill = _get_usuario_by_id(u["id"])
            with st.container():
                st.markdown(f"""
                <div style="background:rgba(133,183,235,0.06);border:1px solid rgba(133,183,235,0.2);
                            border-radius:16px;padding:20px 24px;margin:8px 0 16px;">
                    <h4 style="color:#85B7EB;margin:0 0 16px;">Editando: {u['nom_res']}</h4>
                """, unsafe_allow_html=True)

                datos = _form_usuario(prefill=prefill, key_prefix=f"edit_{u['id']}")

                e1, e2 = st.columns(2)
                with e1:
                    if st.button("💾 Actualizar", use_container_width=True, key=f"btn_upd_{u['id']}"):
                        errores = []
                        if not datos["nom_res"]: errores.append("Nombre requerido.")
                        if not datos["alias"]:   errores.append("Alias requerido.")
                        if not datos["usuario"]: errores.append("Usuario requerido.")
                        if _usuario_existe(datos["usuario"], excluir_id=u["id"]):
                            errores.append(f"El usuario '{datos['usuario']}' ya existe.")

                        if errores:
                            st.session_state.crud_msg = ("error", " | ".join(errores))
                        else:
                            try:
                                _actualizar_usuario(u["id"], datos)
                                st.session_state.crud_msg  = ("ok", f"✔ Usuario '{datos['alias']}' actualizado.")
                                st.session_state.modo_crud  = None
                                st.session_state.uid_editar = None
                            except Exception as e:
                                st.session_state.crud_msg = ("error", f"Error al actualizar: {e}")
                        st.rerun()

                with e2:
                    if st.button("✖ Cancelar", use_container_width=True, key=f"btn_cancel_edit_{u['id']}"):
                        st.session_state.modo_crud  = None
                        st.session_state.uid_editar = None
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

        # ── Confirmación eliminar ────────────────────────────────
        if st.session_state.uid_eliminar == u["id"]:
            st.warning(f"¿Eliminar a **{u['nom_res']}**? Esta acción no se puede deshacer.")
            d1, d2 = st.columns(2)
            with d1:
                if st.button("🗑️ Confirmar eliminación", use_container_width=True,
                             key=f"confirm_del_{u['id']}", type="primary"):
                    try:
                        _eliminar_usuario(u["id"])
                        st.session_state.crud_msg     = ("ok", "✔ Usuario eliminado.")
                        st.session_state.uid_eliminar = None
                    except Exception as e:
                        st.session_state.crud_msg = ("error", f"No se puede eliminar: {e}")
                    st.rerun()
            with d2:
                if st.button("✖ Cancelar", use_container_width=True, key=f"cancel_del_{u['id']}"):
                    st.session_state.uid_eliminar = None
                    st.rerun()