import { useEffect, useMemo, useState } from "react";
import { Edit3, Plus, Trash2, UsersRound } from "lucide-react";
import { api, formatDate } from "../lib/api";
import {
  ConfirmDialog, EmptyState, Field, Loading, Modal, Notice,
  PageHeader, SearchInput, StatusBadge,
} from "../components/UI";

const blank = { nom_res: "", alias: "", usuario: "", password: "", area_id: "", subarea_id: "", rol: "trabajador", estado: "activo" };

export default function Users({ references, refreshReferences }) {
  const [items, setItems] = useState(null);
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const load = () => api("/users").then(setItems).catch((err) => setNotice({ type: "error", text: err.message }));
  useEffect(() => { load(); }, []);
  const filtered = useMemo(() => (items || []).filter((item) =>
    [item.nom_res, item.alias, item.usuario, item.nombre_area, item.nombre_subarea].join(" ").toLowerCase().includes(search.toLowerCase()),
  ), [items, search]);

  const openNew = () => setEditing({ ...blank });
  const openEdit = (item) => setEditing({
    ...item, password: "", area_id: item.area_id || "", subarea_id: item.subarea_id || "",
  });
  const save = async (event) => {
    event.preventDefault(); setBusy(true); setNotice(null);
    try {
      await api(editing.id ? `/users/${editing.id}` : "/users", {
        method: editing.id ? "PUT" : "POST", body: editing,
      });
      setEditing(null); await Promise.all([load(), refreshReferences()]);
      setNotice({ type: "success", text: editing.id ? "Usuario actualizado." : "Usuario creado correctamente." });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  const remove = async () => {
    setBusy(true);
    try {
      await api(`/users/${deleting.id}`, { method: "DELETE" });
      setDeleting(null); await Promise.all([load(), refreshReferences()]);
      setNotice({ type: "success", text: "Usuario eliminado." });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  const subareas = (references?.subareas || []).filter((item) => String(item.area_id) === String(editing?.area_id));

  return (
    <>
      <PageHeader eyebrow="Administración" title="Equipo" subtitle="Personas, accesos y responsabilidades en un solo lugar."
        action={<button className="button button--primary" onClick={openNew}><Plus size={18} />Nuevo usuario</button>} />
      {notice && <Notice type={notice.type} onClose={() => setNotice(null)}>{notice.text}</Notice>}
      <div className="toolbar"><SearchInput value={search} onChange={setSearch} placeholder="Buscar por nombre, usuario o área…" /><span>{filtered.length} usuarios</span></div>
      {!items ? <Loading /> : filtered.length ? (
        <div className="table-panel">
          <div className="data-table data-table--users">
            <div className="data-table__head"><span>Persona</span><span>Usuario</span><span>Área</span><span>Rol</span><span>Estado</span><span>Alta</span><span /></div>
            {filtered.map((item) => (
              <div className="data-table__row" key={item.id}>
                <div className="person-cell"><span className="avatar">{item.alias?.charAt(0) || "U"}</span><div><strong>{item.nom_res}</strong><small>{item.alias}</small></div></div>
                <span className="mono">@{item.usuario}</span>
                <div><strong className="cell-primary">{item.nombre_area || "Sin área"}</strong><small>{item.nombre_subarea || "—"}</small></div>
                <span className={`role role--${item.rol}`}>{item.rol}</span>
                <StatusBadge value={item.estado} />
                <span>{formatDate(item.fecha_creacion)}</span>
                <div className="row-actions">
                  <button onClick={() => openEdit(item)} title="Editar"><Edit3 size={17} /></button>
                  <button className="danger" onClick={() => setDeleting(item)} title="Eliminar"><Trash2 size={17} /></button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : <EmptyState icon={UsersRound} title="No encontramos usuarios" text="Prueba otro término o crea una nueva cuenta." action={<button className="button button--primary" onClick={openNew}><Plus size={17} />Crear usuario</button>} />}

      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing?.id ? "Editar usuario" : "Nuevo usuario"} subtitle="Define sus datos, área y nivel de acceso.">
        {editing && <form onSubmit={save} className="form-grid">
          <Field label="Nombre completo" className="span-2"><input required value={editing.nom_res} onChange={(e) => setEditing({ ...editing, nom_res: e.target.value })} /></Field>
          <Field label="Alias"><input required value={editing.alias} onChange={(e) => setEditing({ ...editing, alias: e.target.value })} /></Field>
          <Field label="Usuario"><input required autoComplete="off" value={editing.usuario} onChange={(e) => setEditing({ ...editing, usuario: e.target.value })} /></Field>
          <Field label={editing.id ? "Nueva contraseña" : "Contraseña"} hint={editing.id ? "Déjala vacía para conservar la actual." : ""} className="span-2">
            <input required={!editing.id} minLength={6} type="password" autoComplete="new-password" value={editing.password} onChange={(e) => setEditing({ ...editing, password: e.target.value })} />
          </Field>
          <Field label="Área"><select value={editing.area_id} onChange={(e) => setEditing({ ...editing, area_id: e.target.value, subarea_id: "" })}><option value="">Sin área</option>{references?.areas?.map((item) => <option key={item.id} value={item.id}>{item.nombre_area}</option>)}</select></Field>
          <Field label="Subárea"><select value={editing.subarea_id} onChange={(e) => setEditing({ ...editing, subarea_id: e.target.value })} disabled={!editing.area_id}><option value="">Sin subárea</option>{subareas.map((item) => <option key={item.id} value={item.id}>{item.nombre_subarea}</option>)}</select></Field>
          <Field label="Rol"><select value={editing.rol} onChange={(e) => setEditing({ ...editing, rol: e.target.value })}><option value="trabajador">Trabajador</option><option value="admin">Administrador</option></select></Field>
          <Field label="Estado"><select value={editing.estado} onChange={(e) => setEditing({ ...editing, estado: e.target.value })}><option value="activo">Activo</option><option value="inactivo">Inactivo</option></select></Field>
          <div className="form-actions span-2"><button type="button" className="button button--ghost" onClick={() => setEditing(null)}>Cancelar</button><button className="button button--primary" disabled={busy}>{busy ? "Guardando…" : "Guardar usuario"}</button></div>
        </form>}
      </Modal>
      <ConfirmDialog open={!!deleting} title="Eliminar usuario" message={`Esta acción eliminará a ${deleting?.nom_res}. Solo será posible si no tiene asignaciones relacionadas.`} onClose={() => setDeleting(null)} onConfirm={remove} busy={busy} />
    </>
  );
}
