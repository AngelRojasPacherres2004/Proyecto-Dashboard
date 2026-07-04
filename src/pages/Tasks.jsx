import { useEffect, useMemo, useState } from "react";
import { CheckSquare2, Edit3, Plus, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { ConfirmDialog, EmptyState, Field, Loading, Modal, Notice, PageHeader, SearchInput } from "../components/UI";

export default function Tasks({ references, refreshReferences }) {
  const [items, setItems] = useState(null);
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const load = () => api("/tasks").then(setItems).catch((err) => setNotice({ type: "error", text: err.message }));
  useEffect(() => { load(); }, []);
  const filtered = useMemo(() => (items || []).filter((item) =>
    `${item.nombre_tarea} ${item.nombre_proyecto}`.toLowerCase().includes(search.toLowerCase()),
  ), [items, search]);
  const save = async (event) => {
    event.preventDefault(); setBusy(true);
    try {
      await api(editing.id ? `/tasks/${editing.id}` : "/tasks", { method: editing.id ? "PUT" : "POST", body: editing });
      setEditing(null); await Promise.all([load(), refreshReferences()]);
      setNotice({ type: "success", text: "Catálogo actualizado." });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  const remove = async () => {
    setBusy(true);
    try {
      await api(`/tasks/${deleting.id}`, { method: "DELETE" });
      setDeleting(null); await Promise.all([load(), refreshReferences()]);
      setNotice({ type: "success", text: "Tarea eliminada." });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  return (
    <>
      <PageHeader eyebrow="Configuración" title="Catálogo de tareas" subtitle="Mantén ordenadas las actividades que tu equipo realiza."
        action={<button className="button button--primary" onClick={() => setEditing({ nombre_tarea: "", proyecto_id: references?.projects?.[0]?.id || "" })}><Plus size={18} />Nueva tarea</button>} />
      {notice && <Notice type={notice.type} onClose={() => setNotice(null)}>{notice.text}</Notice>}
      <div className="toolbar"><SearchInput value={search} onChange={setSearch} placeholder="Buscar tarea o proyecto…" /><span>{filtered.length} tareas</span></div>
      {!items ? <Loading /> : filtered.length ? <div className="cards-list">
        {filtered.map((item) => <article className="task-catalog-card" key={item.id}>
          <span className="catalog-icon"><CheckSquare2 size={20} /></span>
          <div><strong>{item.nombre_tarea}</strong><span>{item.nombre_proyecto}</span></div>
          <small>#{item.id}</small>
          <div className="row-actions"><button onClick={() => setEditing(item)}><Edit3 size={17} /></button><button className="danger" onClick={() => setDeleting(item)}><Trash2 size={17} /></button></div>
        </article>)}
      </div> : <EmptyState icon={CheckSquare2} title="No hay tareas para mostrar" text="Crea la primera actividad del catálogo." />}
      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing?.id ? "Editar tarea" : "Nueva tarea"}>
        {editing && <form onSubmit={save} className="form-grid">
          <Field label="Nombre de la tarea" className="span-2"><input autoFocus required value={editing.nombre_tarea} onChange={(e) => setEditing({ ...editing, nombre_tarea: e.target.value })} /></Field>
          <Field label="Proyecto" className="span-2"><select required value={editing.proyecto_id} onChange={(e) => setEditing({ ...editing, proyecto_id: e.target.value })}><option value="">Seleccionar proyecto</option>{references?.projects?.map((item) => <option key={item.id} value={item.id}>{item.nombre_proyecto}</option>)}</select></Field>
          <div className="form-actions span-2"><button type="button" className="button button--ghost" onClick={() => setEditing(null)}>Cancelar</button><button className="button button--primary" disabled={busy}>Guardar tarea</button></div>
        </form>}
      </Modal>
      <ConfirmDialog open={!!deleting} title="Eliminar tarea" message={`Se eliminará “${deleting?.nombre_tarea}”. No será posible si ya tiene asignaciones.`} onClose={() => setDeleting(null)} onConfirm={remove} busy={busy} />
    </>
  );
}
