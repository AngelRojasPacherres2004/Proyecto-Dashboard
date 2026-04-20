import streamlit as st
from config.db import get_connection
import html

# ================================================================
#  REPOSITORIO
# ================================================================

def _get_empresas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, alias, razon_social, ruc,
            regimen_tributario, regimen_laboral,
            estado_contrato, correo_principal,
            giro_negocio, fecha_registro
        FROM empresas
        ORDER BY razon_social
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def _get_empresa_by_id(eid: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM empresas WHERE id = %s", (eid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def _crear_empresa(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO empresas (
            alias, razon_social, ruc,
            sunat_usuario, sunat_clave,
            regimen_tributario, regimen_laboral,
            afpnet_usuario, afpnet_clave,
            bn_usuario, bn_clave, bn_cta_detraccion,
            giro_negocio, estado_contrato, fecha_contrato,
            correo_principal, digio_ruc, p_electronico
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, (
        data["alias"],          data["razon_social"],     data["ruc"],
        data["sunat_usuario"],  data["sunat_clave"],
        data["regimen_tributario"], data["regimen_laboral"],
        data["afpnet_usuario"], data["afpnet_clave"],
        data["bn_usuario"],     data["bn_clave"],          data["bn_cta_detraccion"],
        data["giro_negocio"],   data["estado_contrato"],   data["fecha_contrato"] or None,
        data["correo_principal"], data["digio_ruc"],       data["p_electronico"],
    ))
    conn.commit()
    cur.close(); conn.close()


def _actualizar_empresa(eid: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE empresas SET
            alias=%s, razon_social=%s, ruc=%s,
            sunat_usuario=%s, sunat_clave=%s,
            regimen_tributario=%s, regimen_laboral=%s,
            afpnet_usuario=%s, afpnet_clave=%s,
            bn_usuario=%s, bn_clave=%s, bn_cta_detraccion=%s,
            giro_negocio=%s, estado_contrato=%s, fecha_contrato=%s,
            correo_principal=%s, digio_ruc=%s, p_electronico=%s
        WHERE id=%s
    """, (
        data["alias"],          data["razon_social"],     data["ruc"],
        data["sunat_usuario"],  data["sunat_clave"],
        data["regimen_tributario"], data["regimen_laboral"],
        data["afpnet_usuario"], data["afpnet_clave"],
        data["bn_usuario"],     data["bn_clave"],          data["bn_cta_detraccion"],
        data["giro_negocio"],   data["estado_contrato"],   data["fecha_contrato"] or None,
        data["correo_principal"], data["digio_ruc"],       data["p_electronico"],
        eid,
    ))
    conn.commit()
    cur.close(); conn.close()


def _eliminar_empresa(eid: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM empresas WHERE id = %s", (eid,))
    conn.commit()
    cur.close(); conn.close()


def _ruc_existe(ruc: str, excluir_id: int = None):
    conn = get_connection()
    cur = conn.cursor()
    if excluir_id:
        cur.execute("SELECT id FROM empresas WHERE ruc=%s AND id!=%s", (ruc, excluir_id))
    else:
        cur.execute("SELECT id FROM empresas WHERE ruc=%s", (ruc,))
    existe = cur.fetchone() is not None
    cur.close(); conn.close()
    return existe


# ================================================================
#  HELPERS UI
# ================================================================
def _badge_estado(estado: str) -> str:
    colores = {
        "Activo":     ("rgba(93,202,165,0.15)",  "#5DCAA5"),
        "Inactivo":   ("rgba(240,149,149,0.15)", "#F09595"),
        "Suspendido": ("rgba(246,194,125,0.15)", "#f6c27d"),
    }
    bg, color = colores.get(estado, ("rgba(255,255,255,0.08)", "white"))
    return f'<span style="background:{bg};color:{color};padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700;">{estado.upper()}</span>'


def _badge_regimen(reg: str) -> str:
    if not reg:
        return '<span style="color:rgba(255,255,255,0.3);font-size:12px;">—</span>'
    color = "#85B7EB" if reg == "GENERAL" else "#f6c27d"
    return f'<span style="color:{color};font-size:12px;font-weight:600;">{reg}</span>'

def _form_empresa(prefill: dict = None, key_prefix: str = "new"):
    """Formulario dividido en tabs para no abrumar."""

    def v(campo, default=""):
        if prefill and prefill.get(campo):
            return prefill[campo]
        return default

    tab1, tab2, tab3 = st.tabs(["📋 Datos generales", "🏦 Credenciales SUNAT / AFP / BN", "📬 Contacto y otros"])

    # ── Tab 1: Datos generales ────────────────────────────────────
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            razon_social = st.text_input("Razón social *", value=v("razon_social"), key=f"{key_prefix}_rs")
            ruc          = st.text_input("RUC *", value=v("ruc"), max_chars=11, key=f"{key_prefix}_ruc")
            regimen_trib = st.selectbox("Régimen tributario",
                                        ["", "GENERAL", "RMT", "RER", "NRUS"],
                                        index=["", "GENERAL", "RMT", "RER", "NRUS"].index(v("regimen_tributario"))
                                        if v("regimen_tributario") in ["", "GENERAL", "RMT", "RER", "NRUS"] else 0,
                                        key=f"{key_prefix}_rt")
        with c2:
            alias        = st.text_input("Alias", value=v("alias"), key=f"{key_prefix}_alias")
            regimen_lab  = st.selectbox("Régimen laboral",
                                        ["", "RG", "REMYPE"],
                                        index=["", "RG", "REMYPE"].index(v("regimen_laboral"))
                                        if v("regimen_laboral") in ["", "RG", "REMYPE"] else 0,
                                        key=f"{key_prefix}_rl")
            estado_contrato = st.selectbox("Estado contrato",
                                        ["Activo", "Inactivo", "Suspendido"],
                                        index=["Activo", "Inactivo", "Suspendido"].index(v("estado_contrato", "Activo"))
                                        if v("estado_contrato", "Activo") in ["Activo", "Inactivo", "Suspendido"] else 0,
                                        key=f"{key_prefix}_ec")

        fecha_raw = v("fecha_contrato")
        fecha_contrato = st.date_input("Fecha contrato",
                                    value=fecha_raw if fecha_raw else None,
                                    key=f"{key_prefix}_fc",
                                    format="DD/MM/YYYY")

        giro_negocio = st.text_area("Giro de negocio", value=v("giro_negocio"), height=80, key=f"{key_prefix}_giro")

    # ── Tab 2: Credenciales ───────────────────────────────────────
    with tab2:
        st.markdown("""<p style="color:rgba(255,255,255,0.4);font-size:12px;margin-bottom:12px;">SUNAT SOL</p>""", unsafe_allow_html=True)
        sc1, sc2 = st.columns(2)
        with sc1:
            sunat_usuario = st.text_input("Usuario SUNAT", value=v("sunat_usuario"), key=f"{key_prefix}_su")
        with sc2:
            sunat_clave   = st.text_input("Clave SUNAT",   value=v("sunat_clave"),   key=f"{key_prefix}_sc")

        st.markdown("""<p style="color:rgba(255,255,255,0.4);font-size:12px;margin:12px 0;">AFP NET</p>""", unsafe_allow_html=True)
        ac1, ac2 = st.columns(2)
        with ac1:
            afpnet_usuario = st.text_input("Usuario AFP Net", value=v("afpnet_usuario"), key=f"{key_prefix}_au")
        with ac2:
            afpnet_clave   = st.text_input("Clave AFP Net",   value=v("afpnet_clave"),   key=f"{key_prefix}_ac")

        st.markdown("""<p style="color:rgba(255,255,255,0.4);font-size:12px;margin:12px 0;">BANCO DE LA NACIÓN</p>""", unsafe_allow_html=True)
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            bn_usuario = st.text_input("Usuario BN",        value=v("bn_usuario"),        key=f"{key_prefix}_bu")
        with bc2:
            bn_clave   = st.text_input("Clave BN",          value=v("bn_clave"),          key=f"{key_prefix}_bc")
        with bc3:
            bn_cta     = st.text_input("Cta. Detracción BN", value=v("bn_cta_detraccion"), key=f"{key_prefix}_bct")

        st.markdown("""<p style="color:rgba(255,255,255,0.4);font-size:12px;margin:12px 0;">DIGIO / PADRÓN</p>""", unsafe_allow_html=True)
        dc1, dc2 = st.columns(2)
        with dc1:
            digio_ruc    = st.text_input("Dígito RUC",       value=v("digio_ruc"),    key=f"{key_prefix}_dr")
        with dc2:
            p_electronico = st.text_input("Padrón electrónico", value=v("p_electronico"), key=f"{key_prefix}_pe")

    # ── Tab 3: Contacto ───────────────────────────────────────────
    with tab3:
        correo_principal = st.text_input("Correo principal", value=v("correo_principal"), key=f"{key_prefix}_cp")

    return {
        "alias":              alias.strip().upper(),
        "razon_social":       razon_social.strip().upper(),
        "ruc":                ruc.strip(),
        "sunat_usuario":      sunat_usuario.strip(),
        "sunat_clave":        sunat_clave.strip(),
        "regimen_tributario": regimen_trib,
        "regimen_laboral":    regimen_lab,
        "afpnet_usuario":     afpnet_usuario.strip(),
        "afpnet_clave":       afpnet_clave.strip(),
        "bn_usuario":         bn_usuario.strip(),
        "bn_clave":           bn_clave.strip(),
        "bn_cta_detraccion":  bn_cta.strip(),
        "giro_negocio":       giro_negocio.strip(),
        "estado_contrato":    estado_contrato,
        "fecha_contrato":     fecha_contrato,
        "correo_principal":   correo_principal.strip(),
        "digio_ruc":          digio_ruc.strip(),
        "p_electronico":      p_electronico.strip(),
    }


# ================================================================
#  VISTA PRINCIPAL
# ================================================================

def admin_empresas():

    st.markdown("""
    <div style="margin-bottom:24px;">
        <h2 style="color:#f6c27d;font-size:22px;font-weight:800;margin:0;">Gestión de Empresas</h2>
        <p style="color:rgba(255,255,255,0.5);font-size:13px;margin-top:4px;">
            Administra las empresas clientes del estudio contable
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Inicializar estados ──────────────────────────────────────
    for key in ["emp_modo", "emp_id_editar", "emp_id_eliminar", "emp_msg"]:
        if key not in st.session_state:
            st.session_state[key] = None

    # ── Mensaje de feedback ──────────────────────────────────────
    if st.session_state.emp_msg:
        tipo, texto = st.session_state.emp_msg
        (st.success if tipo == "ok" else st.error)(texto)
        st.session_state.emp_msg = None

    # ── Barra superior ───────────────────────────────────────────
    col_busq, col_btn = st.columns([3, 1])
    with col_busq:
        busqueda = st.text_input("🔍 Buscar por razón social, RUC o alias",
                                placeholder="Escribe para filtrar...",
                                label_visibility="collapsed")
    with col_btn:
        if st.button("➕ Nueva empresa", use_container_width=True):
            st.session_state.emp_modo     = "crear"
            st.session_state.emp_id_editar = None

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ================================================================
    #  FORMULARIO CREAR
    # ================================================================
    if st.session_state.emp_modo == "crear":
        st.markdown("""
        <div style="background:rgba(246,194,125,0.06);border:1px solid rgba(246,194,125,0.2);
                    border-radius:16px;padding:20px 24px;margin-bottom:20px;">
            <h4 style="color:#f6c27d;margin:0 0 16px;">Nueva empresa</h4>
        </div>
        """, unsafe_allow_html=True)

        datos = _form_empresa(key_prefix="crear")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Guardar", use_container_width=True, key="btn_crear_emp"):
                errores = []
                if not datos["razon_social"]: errores.append("Razón social requerida.")
                if not datos["ruc"]:          errores.append("RUC requerido.")
                if len(datos["ruc"]) != 11:   errores.append("RUC debe tener 11 dígitos.")
                if _ruc_existe(datos["ruc"]):  errores.append(f"El RUC {datos['ruc']} ya existe.")

                if errores:
                    st.session_state.emp_msg = ("error", " | ".join(errores))
                else:
                    try:
                        _crear_empresa(datos)
                        st.session_state.emp_msg  = ("ok", f"✅ Empresa '{datos['razon_social']}' creada.")
                        st.session_state.emp_modo = None
                    except Exception as e:
                        st.session_state.emp_msg = ("error", f"Error al crear: {e}")
                st.rerun()
        with c2:
            if st.button("✖ Cancelar", use_container_width=True, key="btn_cancel_crear_emp"):
                st.session_state.emp_modo = None
                st.rerun()

    # ================================================================
    #  TABLA DE EMPRESAS
    # ================================================================
    empresas = _get_empresas()

    if busqueda:
        q = busqueda.lower()
        empresas = [e for e in empresas if
                    q in e["razon_social"].lower() or
                    q in e["ruc"] or
                    q in (e["alias"] or "").lower()]

    if not empresas:
        st.info("No se encontraron empresas.")
        return

    # Mostrar tabla de empresas
    st.markdown("### 📋 Lista de Empresas")
    
    # Encabezado de la tabla
    with st.container(border=False):
        col1, col2, col3, col4, col5, col6 = st.columns([2.5, 1, 1, 1, 1, 0.8])
        with col1:
            st.markdown("<span style='color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;'>RAZÓN SOCIAL</span>", unsafe_allow_html=True)
        with col2:
            st.markdown("<span style='color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;'>RUC</span>", unsafe_allow_html=True)
        with col3:
            st.markdown("<span style='color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;'>RÉGIMEN</span>", unsafe_allow_html=True)
        with col4:
            st.markdown("<span style='color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;'>LABORAL</span>", unsafe_allow_html=True)
        with col5:
            st.markdown("<span style='color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;'>ESTADO</span>", unsafe_allow_html=True)
        with col6:
            st.markdown("<span style='color:rgba(255,255,255,0.5);font-weight:600;font-size:12px;'>ACCIONES</span>", unsafe_allow_html=True)
    
    st.divider()
    
    for e in empresas:
        # Usar contenedor para cada fila
        with st.container(border=True):
            col1, col2, col3, col4, col5, col6 = st.columns([2.5, 1, 1, 1, 1, 0.8])
            
            # Columna 1: Razón social
            with col1:
                st.markdown(f"""
                <div>
                    <span style="color:white;font-weight:600;font-size:14px;">{e['razon_social']}</span>
                    {'<br><span style="color:rgba(255,255,255,0.35);font-size:11px;">' + e['alias'] + '</span>' if e.get('alias') else ''}
                </div>
                """, unsafe_allow_html=True)
            
            # Columna 2: RUC
            with col2:
                st.caption(e['ruc'])
            
            # Columna 3: Régimen tributario
            with col3:
                st.markdown(_badge_regimen(e.get('regimen_tributario')), unsafe_allow_html=True)
            
            # Columna 4: Régimen laboral
            with col4:
                st.caption(e.get('regimen_laboral') or '—')
            
            # Columna 5: Estado
            with col5:
                st.markdown(_badge_estado(e.get('estado_contrato', 'Activo')), unsafe_allow_html=True)
            
            # Columna 6: Botones
            with col6:
                col_edit, col_del = st.columns(2, gap="small")
                with col_edit:
                    if st.button("✏️", key=f"edit_emp_{e['id']}", help="Editar", use_container_width=True):
                        st.session_state.emp_modo      = "editar"
                        st.session_state.emp_id_editar = e["id"]
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_emp_{e['id']}", help="Eliminar", use_container_width=True):
                        st.session_state.emp_id_eliminar = e["id"]
                        st.rerun()

        # ── Formulario editar inline ─────────────────────────────
        if st.session_state.emp_modo == "editar" and st.session_state.emp_id_editar == e["id"]:
            prefill = _get_empresa_by_id(e["id"])
            st.markdown(f"""
            <div style="background:rgba(133,183,235,0.06);border:1px solid rgba(133,183,235,0.2);
                        border-radius:16px;padding:20px 24px;margin:8px 0 16px;">
                <h4 style="color:#85B7EB;margin:0 0 16px;">Editando: {e['razon_social']}</h4>
            </div>
            """, unsafe_allow_html=True)

            datos = _form_empresa(prefill=prefill, key_prefix=f"edit_emp_{e['id']}")

            e1, e2 = st.columns(2)
            with e1:
                if st.button("💾 Actualizar", use_container_width=True, key=f"btn_upd_emp_{e['id']}"):
                    errores = []
                    if not datos["razon_social"]: errores.append("Razón social requerida.")
                    if not datos["ruc"]:          errores.append("RUC requerido.")
                    if len(datos["ruc"]) != 11:   errores.append("RUC debe tener 11 dígitos.")
                    if _ruc_existe(datos["ruc"], excluir_id=e["id"]):
                        errores.append(f"El RUC {datos['ruc']} ya pertenece a otra empresa.")

                    if errores:
                        st.session_state.emp_msg = ("error", " | ".join(errores))
                    else:
                        try:
                            _actualizar_empresa(e["id"], datos)
                            st.session_state.emp_msg       = ("ok", f"✅ Empresa actualizada.")
                            st.session_state.emp_modo      = None
                            st.session_state.emp_id_editar = None
                        except Exception as ex:
                            st.session_state.emp_msg = ("error", f"Error al actualizar: {ex}")
                    st.rerun()
            with e2:
                if st.button("✖ Cancelar", use_container_width=True, key=f"btn_cancel_edit_emp_{e['id']}"):
                    st.session_state.emp_modo      = None
                    st.session_state.emp_id_editar = None
                    st.rerun()

        # ── Confirmación eliminar ────────────────────────────────
        if st.session_state.emp_id_eliminar == e["id"]:
            st.warning(f"¿Eliminar **{e['razon_social']}**? Se eliminarán también sus accesos asociados.")
            d1, d2 = st.columns(2)
            with d1:
                if st.button("🗑️ Confirmar", use_container_width=True,
                            key=f"confirm_del_emp_{e['id']}", type="primary"):
                    try:
                        _eliminar_empresa(e["id"])
                        st.session_state.emp_msg         = ("ok", "✅ Empresa eliminada.")
                        st.session_state.emp_id_eliminar = None
                    except Exception as ex:
                        st.session_state.emp_msg = ("error", f"No se puede eliminar: {ex}")
                    st.rerun()
            with d2:
                if st.button("✖ Cancelar", use_container_width=True, key=f"cancel_del_emp_{e['id']}"):
                    st.session_state.emp_id_eliminar = None
                    st.rerun()