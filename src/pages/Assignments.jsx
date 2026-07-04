import { useEffect, useMemo, useState } from "react";
import { CalendarClock, Edit3, Plus, Trash2, UserRound } from "lucide-react";
import { api, formatDate, todayISO } from "../lib/api";
import {
  ConfirmDialog, EmptyState, Field, Loading, Modal, Notice, PageHeader,
  Pagination, SearchInput, StatusBadge,
} from "../components/UI";

const initial = { usuario_ids: [], empresa_id: "", tarea_id: "", fecha_meta: todayISO(), estado: "pendiente", peso: 1 };
const perPage = 10;

export default function Assignments({ references }) {
  const [items, setItems] = useState(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [period, setPeriod] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const load = () => api("/assignments").then(setItems).catch((err) => setNotice({ type: "error", text: err.message }));
  useEffect(() => { load(); }, []);
  const filtered = useMemo(() => (items || []).filter((item) => {
    const matchesText = [item.empresa, item.tarea, item.proyecto, ...item.trabajadores.map((u) => u.trabajador)].join(" ").toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !status || item.estado === status;
    const matchesPeriod = !period || String(item.fecha_meta).slice(0, 7) === period;
    return matchesText && matchesStatus && matchesPeriod;
  }), [items, search, status, period]);
  useEffect(() => setPage(1), [search, status, period]);
  const pages = Math.max(1, Math.ceil(filtered.length / perPage));
  const visible = filtered.slice((page - 1) * perPage, page * perPage);
  const metrics = {
    total: items?.length || 0,
    pendientes: items?.filter((x) => x.estado === "pendiente").length || 0,
    completadas: items?.filter((x) => x.estado === "completada").length || 0,
    vencidas: items?.filter((x) => x.estado === "vencida").length || 0,
  };
  const openEdit = (item) => setEditing({
    id: item.id, empresa_id: item.empresa_id, tarea_id: item.tarea_id,
    fecha_meta: String(item.fecha_meta).slice(0, 10), estado: item.estado,
    peso: item.peso, usuario_ids: item.trabajadores.map((u) => u.usuario_id),
  });
  const toggleUser = (id) => setEditing((current) => ({
    ...current,
    usuario_ids: current.usuario_ids.includes(id)
      ? current.usuario_ids.filter((item) => item !== id)
      : [...current.usuario_ids, id],
  }));
  const save = async (event) => {
    event.preventDefault(); setBusy(true); setNotice(null);
    try {
      await api(editing.id ? `/assignments/${editing.id}` : "/assignments", {
        method: editing.id ? "PUT" : "POST", body: editing,
      });
      setEditing(null); await load();
      setNotice({ type: "success", text: editing.id ? "Asignación actualizada." : "Asignación creada." });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  const remove = async () => {
    setBusy(true);
    try {
      await api(`/assignments/${deleting.id}`, { method: "DELETE" });
      setDeleting(null); await load();
      setNotice({ type: "success", text: "Asignación eliminada." });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };

  return (
    <>
      <PageHeader eyebrow="Operación" title="Asignaciones" subtitle="Distribuye el trabajo y acompaña cada vencimiento."
        action={<button className="button button--primary" onClick={() => setEditing({ ...initial })}><Plus size={18} />Nueva asignación</button>} />
      {notice && <Notice type={notice.type} onClose={() => setNotice(null)}>{notice.text}</Notice>}
      <section className="compact-metrics">
        <div><span>Total</span><strong>{metrics.total}</strong></div>
        <div className="amber"><span>Pendientes</span><strong>{metrics.pendientes}</strong></div>
        <div className="green"><span>Completadas</span><strong>{metrics.completadas}</strong></div>
        <div className="red"><span>Vencidas</span><strong>{metrics.vencidas}</strong></div>
      </section>
      <div className="toolbar toolbar--filters">
        <SearchInput value={search} onChange={setSearch} placeholder="Buscar empresa, tarea o persona…" />
        <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Todos los estados</option><option value="pendiente">Pendiente</option><option value="completada">Completada</option><option value="vencida">Vencida</option></select>
        <input type="month" value={period} onChange={(e) => setPeriod(e.target.value)} />
      </div>
      {!items ? <Loading /> : visible.length ? <div className="assignment-list">
        {visible.map((item) => {
          const due = new Date(`${String(item.fecha_meta).slice(0, 10)}T12:00:00`);
          const overdue = item.estado !== "completada" && due < new Date();
          return <article className="assignment-card" key={item.id}>
            <div className="assignment-id"><small>Asignación</small><strong>#{item.id}</strong></div>
            <div className="assignment-main"><span className="assignment-project">{item.proyecto}</span><h3>{item.tarea}</h3><p>{item.empresa}</p></div>
            <div className="assignment-people">
              <div className="avatar-stack">{item.trabajadores.slice(0, 3).map((person) => <span key={person.usuario_id} title={person.trabajador}>{person.alias?.charAt(0) || "U"}</span>)}{item.trabajadores.length > 3 && <i>+{item.trabajadores.length - 3}</i>}</div>
              <small>{item.trabajadores.length} {item.trabajadores.length === 1 ? "responsable" : "responsables"}</small>
            </div>
            <div className={`assignment-date ${overdue ? "overdue" : ""}`}><CalendarClock size={17} /><div><small>Fecha meta</small><strong>{formatDate(item.fecha_meta)}</strong></div></div>
            <StatusBadge value={overdue && item.estado === "pendiente" ? "vencida" : item.estado} />
            <div className="row-actions"><button onClick={() => openEdit(item)}><Edit3 size={17} /></button><button className="danger" onClick={() => setDeleting(item)}><Trash2 size={17} /></button></div>
          </article>;
        })}
        <Pagination page={page} pages={pages} onChange={setPage} />
      </div> : <EmptyState icon={CalendarClock} title="No hay asignaciones" text="No encontramos resultados con estos filtros." />}

      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing?.id ? `Editar asignación #${editing.id}` : "Nueva asignación"} subtitle="Una asignación puede tener varios responsables." wide>
        {editing && <form onSubmit={save} className="form-grid">
          <Field label="Empresa"><select required value={editing.empresa_id} onChange={(e) => setEditing({ ...editing, empresa_id: e.target.value })}><option value="">Seleccionar empresa</option>{references?.companies?.map((item) => <option key={item.id} value={item.id}>{item.alias} · {item.razon_social}</option>)}</select></Field>
          <Field label="Tarea"><select required value={editing.tarea_id} onChange={(e) => setEditing({ ...editing, tarea_id: e.target.value })}><option value="">Seleccionar tarea</option>{references?.tasks?.map((item) => <option key={item.id} value={item.id}>{item.nombre_proyecto} · {item.nombre_tarea}</option>)}</select></Field>
          <Field label="Fecha meta"><input required type="date" value={editing.fecha_meta} onChange={(e) => setEditing({ ...editing, fecha_meta: e.target.value })} /></Field>
          <Field label="Peso"><input required min="1" max="10" type="number" value={editing.peso} onChange={(e) => setEditing({ ...editing, peso: Number(e.target.value) })} /></Field>
          {editing.id && <Field label="Estado" className="span-2"><select value={editing.estado} onChange={(e) => setEditing({ ...editing, estado: e.target.value })}><option value="pendiente">Pendiente</option><option value="completada">Completada</option><option value="vencida">Vencida</option></select></Field>}
          <div className="field span-2"><span>Responsables</span><div className="people-picker">
            {references?.users?.map((person) => <button type="button" key={person.id} className={editing.usuario_ids.includes(person.id) ? "selected" : ""} onClick={() => toggleUser(person.id)}>
              <span><UserRound size={16} /></span><div><strong>{person.nom_res}</strong><small>{person.alias}</small></div><i />
            </button>)}
          </div><small>{editing.usuario_ids.length} seleccionados</small></div>
          <div className="form-actions span-2"><button type="button" className="button button--ghost" onClick={() => setEditing(null)}>Cancelar</button><button className="button button--primary" disabled={busy}>{busy ? "Guardando…" : "Guardar asignación"}</button></div>
        </form>}
      </Modal>
      <ConfirmDialog open={!!deleting} title="Eliminar asignación" message={`Se eliminará la asignación #${deleting?.id} para todos sus responsables.`} onClose={() => setDeleting(null)} onConfirm={remove} busy={busy} />
    </>
  );
}
