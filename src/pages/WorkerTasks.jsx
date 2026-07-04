import { useEffect, useMemo, useState } from "react";
import { Building2, CalendarClock, CheckCircle2, ChevronRight, ClipboardList, Target } from "lucide-react";
import { api, formatDate, todayISO } from "../lib/api";
import { EmptyState, Field, Loading, Modal, Notice, PageHeader, StatusBadge } from "../components/UI";

export default function WorkerTasks() {
  const [items, setItems] = useState(null);
  const [filter, setFilter] = useState("activas");
  const [detail, setDetail] = useState(null);
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const load = () => api("/worker/tasks").then(setItems).catch((err) => setNotice({ type: "error", text: err.message }));
  useEffect(() => { load(); }, []);
  const filtered = useMemo(() => (items || []).filter((item) =>
    filter === "todas" || (filter === "completadas" ? item.estado === "completada" : item.estado !== "completada"),
  ), [items, filter]);
  const open = async (item) => {
    setBusy(true);
    try {
      const data = await api(`/worker/tasks/${item.id}`);
      setDetail(data);
      setForm({ estado: data.estado, fecha_realizada: data.fecha_realizada?.slice(0, 10) || todayISO() });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  const save = async (event) => {
    event.preventDefault(); setBusy(true);
    try {
      const result = await api(`/worker/tasks/${detail.id}`, { method: "PUT", body: form });
      setDetail(null); setForm(null); await load();
      setNotice({ type: "success", text: `Progreso guardado. Rendimiento: ${result.rendimiento}.` });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  const pending = items?.filter((item) => item.estado !== "completada").length || 0;
  const completed = items?.filter((item) => item.estado === "completada").length || 0;

  return (
    <>
      <PageHeader eyebrow="Mi espacio" title="Mis tareas" subtitle="Tus prioridades, fechas y avances en una vista tranquila." />
      {notice && <Notice type={notice.type} onClose={() => setNotice(null)}>{notice.text}</Notice>}
      <section className="worker-summary">
        <div><span className="worker-summary__icon amber"><CalendarClock /></span><div><small>Por completar</small><strong>{pending}</strong></div></div>
        <div><span className="worker-summary__icon green"><CheckCircle2 /></span><div><small>Completadas</small><strong>{completed}</strong></div></div>
        <div><span className="worker-summary__icon blue"><Target /></span><div><small>Total asignado</small><strong>{items?.length || 0}</strong></div></div>
      </section>
      <div className="segmented">
        <button className={filter === "activas" ? "active" : ""} onClick={() => setFilter("activas")}>Activas</button>
        <button className={filter === "completadas" ? "active" : ""} onClick={() => setFilter("completadas")}>Completadas</button>
        <button className={filter === "todas" ? "active" : ""} onClick={() => setFilter("todas")}>Todas</button>
      </div>
      {!items ? <Loading /> : filtered.length ? <div className="worker-task-grid">
        {filtered.map((item) => {
          const days = Math.ceil((new Date(`${String(item.fecha_limite).slice(0, 10)}T23:59:00`) - new Date()) / 86_400_000);
          return <button className="worker-task" key={`${item.id}-${item.titulo}`} onClick={() => open(item)} disabled={busy}>
            <div className="worker-task__top"><span>{item.proyecto}</span><StatusBadge value={item.estado} /></div>
            <h3>{item.titulo}</h3><p><Building2 size={16} />{item.empresa}</p>
            <div className="worker-task__footer">
              <div className={days < 0 && item.estado !== "completada" ? "late" : ""}><CalendarClock size={17} /><span><small>Fecha meta</small><strong>{formatDate(item.fecha_limite)}</strong></span></div>
              <ChevronRight size={20} />
            </div>
          </button>;
        })}
      </div> : <EmptyState icon={ClipboardList} title="No hay tareas en esta vista" text={filter === "activas" ? "Buen trabajo: no tienes pendientes." : "Todavía no hay tareas completadas."} />}
      <Modal open={!!detail} onClose={() => setDetail(null)} title={detail?.tarea || "Detalle de tarea"} subtitle={detail ? `${detail.proyecto} · Asignación #${detail.id}` : ""}>
        {detail && form && <form onSubmit={save}>
          <div className="task-detail-summary">
            <div><span>Empresa</span><strong>{detail.empresa}</strong><small>RUC {detail.ruc}</small></div>
            <div><span>Fecha meta</span><strong>{formatDate(detail.fecha_meta)}</strong><small>Peso {detail.peso}</small></div>
          </div>
          <div className="form-grid">
            <Field label="Actualizar estado"><select value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}><option value="pendiente">Pendiente</option>{form.estado === "vencida" && <option value="vencida">Vencida</option>}<option value="completada">Completada</option></select></Field>
            {form.estado === "completada" && <Field label="Fecha realizada"><input required max={todayISO()} type="date" value={form.fecha_realizada} onChange={(e) => setForm({ ...form, fecha_realizada: e.target.value })} /></Field>}
            <div className="form-note span-2">Al completar una tarea compartida, el sistema registra el avance de todo el grupo y calcula el rendimiento según la fecha meta.</div>
            <div className="form-actions span-2"><button type="button" className="button button--ghost" onClick={() => setDetail(null)}>Cancelar</button><button className="button button--primary" disabled={busy}>{busy ? "Guardando…" : "Guardar progreso"}</button></div>
          </div>
        </form>}
      </Modal>
    </>
  );
}
