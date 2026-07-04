import { useEffect, useMemo, useState } from "react";
import { CalendarDays, CheckCircle2, ChevronLeft, ChevronRight, Plus, Printer, Sparkles, UserPlus } from "lucide-react";
import { api } from "../lib/api";
import { EmptyState, Field, Loading, Modal, Notice, PageHeader, StatusBadge } from "../components/UI";

const monthNames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
const weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
const groups = [
  { key: "0", label: "RUC termina en 0" }, { key: "1", label: "RUC termina en 1" },
  { key: "23", label: "RUC termina en 2 o 3" }, { key: "45", label: "RUC termina en 4 o 5" },
  { key: "67", label: "RUC termina en 6 o 7" }, { key: "89", label: "RUC termina en 8 o 9" },
];
const initialDates = { 0: "", 1: "", 23: "", 45: "", 67: "", 89: "" };

function groupForRuc(ruc) {
  const digit = String(ruc || "").slice(-1);
  if (["0", "1"].includes(digit)) return digit;
  if (["2", "3"].includes(digit)) return "23";
  if (["4", "5"].includes(digit)) return "45";
  if (["6", "7"].includes(digit)) return "67";
  if (["8", "9"].includes(digit)) return "89";
  return null;
}

export default function Schedule({ references }) {
  const today = new Date();
  const [cursor, setCursor] = useState({ month: today.getMonth() + 1, year: today.getFullYear() });
  const [items, setItems] = useState(null);
  const [generator, setGenerator] = useState(null);
  const [assigning, setAssigning] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const load = () => {
    setItems(null);
    api(`/schedule?month=${cursor.month}&year=${cursor.year}`).then(setItems).catch((err) => setNotice({ type: "error", text: err.message }));
  };
  useEffect(() => {
    setItems(null);
    api(`/schedule?month=${cursor.month}&year=${cursor.year}`)
      .then(setItems)
      .catch((err) => setNotice({ type: "error", text: err.message }));
  }, [cursor.month, cursor.year]);
  const moveMonth = (amount) => {
    const date = new Date(cursor.year, cursor.month - 1 + amount, 1);
    setCursor({ month: date.getMonth() + 1, year: date.getFullYear() });
  };
  const calendar = useMemo(() => {
    const firstDay = new Date(cursor.year, cursor.month - 1, 1);
    const start = (firstDay.getDay() + 6) % 7;
    const count = new Date(cursor.year, cursor.month, 0).getDate();
    return [...Array(start).fill(null), ...Array.from({ length: count }, (_, i) => i + 1)];
  }, [cursor]);
  const byDay = useMemo(() => (items || []).reduce((map, item) => {
    const day = new Date(`${String(item.fecha_vencimiento).slice(0, 10)}T12:00:00`).getDate();
    map[day] = [...(map[day] || []), item]; return map;
  }, {}), [items]);
  const generate = async (event) => {
    event.preventDefault(); setBusy(true);
    try {
      const rows = references.companies.map((company) => ({
        tarea_id: generator.tarea_id,
        empresa_id: company.id,
        periodo_mes: Number(generator.periodo_mes),
        periodo_anio: Number(generator.periodo_anio),
        fecha_vencimiento: generator.dates[groupForRuc(company.ruc)],
      })).filter((row) => row.fecha_vencimiento);
      const result = await api("/schedule/import", { method: "POST", body: { rows } });
      setGenerator(null); await load();
      setNotice({ type: "success", text: `${result.inserted} vencimientos creados; ${result.skipped} ya existían.` });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  const toggleUser = (id) => setAssigning((current) => ({
    ...current, usuario_ids: current.usuario_ids.includes(id) ? current.usuario_ids.filter((x) => x !== id) : [...current.usuario_ids, id],
  }));
  const assign = async (event) => {
    event.preventDefault(); setBusy(true);
    try {
      await api(`/schedule/${assigning.id}/assign`, { method: "POST", body: assigning });
      setAssigning(null); await load();
      setNotice({ type: "success", text: "Responsables asignados correctamente." });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };

  return (
    <>
      <PageHeader eyebrow="Planificación tributaria" title="Cronograma" subtitle="Convierte fechas SUNAT en trabajo organizado para el equipo."
        action={<div className="header-actions"><button className="button button--ghost" onClick={() => window.print()}><Printer size={17} />Imprimir</button><button className="button button--primary" onClick={() => setGenerator({ tarea_id: "", periodo_mes: cursor.month, periodo_anio: cursor.year, dates: { ...initialDates } })}><Sparkles size={17} />Generar vencimientos</button></div>} />
      {notice && <Notice type={notice.type} onClose={() => setNotice(null)}>{notice.text}</Notice>}
      <section className="calendar-panel">
        <header className="calendar-toolbar">
          <button onClick={() => moveMonth(-1)}><ChevronLeft size={20} /></button>
          <div><span>Calendario mensual</span><h2>{monthNames[cursor.month - 1]} {cursor.year}</h2></div>
          <button onClick={() => moveMonth(1)}><ChevronRight size={20} /></button>
        </header>
        {!items ? <Loading /> : <>
          <div className="calendar-weekdays">{weekdays.map((day) => <span key={day}>{day}</span>)}</div>
          <div className="calendar-grid">
            {calendar.map((day, index) => <div className={`calendar-day ${!day ? "calendar-day--empty" : ""}`} key={`${day}-${index}`}>
              {day && <><span className={day === today.getDate() && cursor.month === today.getMonth() + 1 && cursor.year === today.getFullYear() ? "today" : ""}>{day}</span>
                <div className="calendar-events">{(byDay[day] || []).slice(0, 3).map((item) => <button key={item.id} className={item.asignado ? "assigned" : ""} onClick={() => !item.asignado && setAssigning({ ...item, usuario_ids: [], peso: 1 })}>
                  <i /> <strong>{item.empresa}</strong><small>{item.tarea}</small>
                </button>)}{(byDay[day] || []).length > 3 && <em>+{byDay[day].length - 3} más</em>}</div>
              </>}
            </div>)}
          </div>
        </>}
      </section>
      <section className="schedule-list panel">
        <header className="panel__header"><div><h2>Vencimientos del mes</h2><p>{items?.length || 0} registros planificados</p></div></header>
        {items?.length ? items.map((item) => <div className="schedule-row" key={item.id}>
          <time><strong>{String(new Date(`${String(item.fecha_vencimiento).slice(0, 10)}T12:00:00`).getDate()).padStart(2, "0")}</strong><span>{monthNames[cursor.month - 1].slice(0, 3)}</span></time>
          <div><strong>{item.empresa}</strong><small>{item.razon_social} · RUC {item.ruc}</small></div>
          <div><strong>{item.tarea}</strong><small>{item.proyecto}</small></div>
          <StatusBadge value={item.asignado ? "Asignado" : "Pendiente"} />
          {!item.asignado ? <button className="button button--soft button--small" onClick={() => setAssigning({ ...item, usuario_ids: [], peso: 1 })}><UserPlus size={16} />Asignar</button> : <span className="assigned-check"><CheckCircle2 size={17} />Listo</span>}
        </div>) : items && <EmptyState icon={CalendarDays} title="Este mes aún está libre" text="Genera los vencimientos usando las fechas publicadas por SUNAT." />}
      </section>

      <Modal open={!!generator} onClose={() => setGenerator(null)} title="Generar vencimientos" subtitle="Transcribe una vez las fechas de la tabla SUNAT; Nexo las aplica según el último dígito del RUC." wide>
        {generator && <form onSubmit={generate} className="form-grid">
          <Field label="Tarea"><select required value={generator.tarea_id} onChange={(e) => setGenerator({ ...generator, tarea_id: e.target.value })}><option value="">Seleccionar obligación</option>{references?.tasks?.map((item) => <option key={item.id} value={item.id}>{item.nombre_proyecto} · {item.nombre_tarea}</option>)}</select></Field>
          <Field label="Periodo"><div className="inline-fields"><select value={generator.periodo_mes} onChange={(e) => setGenerator({ ...generator, periodo_mes: e.target.value })}>{monthNames.map((name, i) => <option key={name} value={i + 1}>{name}</option>)}</select><input type="number" min="2024" max="2100" value={generator.periodo_anio} onChange={(e) => setGenerator({ ...generator, periodo_anio: e.target.value })} /></div></Field>
          <div className="form-section-title span-2"><strong>Fechas según último dígito del RUC</strong><span>Las empresas activas se distribuirán automáticamente.</span></div>
          {groups.map((group) => <Field key={group.key} label={group.label}><input required type="date" value={generator.dates[group.key]} onChange={(e) => setGenerator({ ...generator, dates: { ...generator.dates, [group.key]: e.target.value } })} /></Field>)}
          <div className="generator-preview span-2"><Plus size={18} /><span>Se prepararán hasta <strong>{references?.companies?.length || 0} vencimientos</strong> sin duplicar los existentes.</span></div>
          <div className="form-actions span-2"><button type="button" className="button button--ghost" onClick={() => setGenerator(null)}>Cancelar</button><button className="button button--primary" disabled={busy}>{busy ? "Generando…" : "Generar cronograma"}</button></div>
        </form>}
      </Modal>
      <Modal open={!!assigning} onClose={() => setAssigning(null)} title="Asignar responsables" subtitle={assigning ? `${assigning.empresa} · ${assigning.tarea}` : ""}>
        {assigning && <form onSubmit={assign} className="form-grid">
          <div className="field span-2"><span>Colaboradores</span><div className="people-picker">
            {references?.users?.map((person) => <button type="button" key={person.id} className={assigning.usuario_ids.includes(person.id) ? "selected" : ""} onClick={() => toggleUser(person.id)}><span>{person.alias?.charAt(0)}</span><div><strong>{person.nom_res}</strong><small>{person.alias}</small></div><i /></button>)}
          </div></div>
          <Field label="Peso de la tarea" className="span-2"><input type="number" min="1" max="10" value={assigning.peso} onChange={(e) => setAssigning({ ...assigning, peso: Number(e.target.value) })} /></Field>
          <div className="form-actions span-2"><button type="button" className="button button--ghost" onClick={() => setAssigning(null)}>Cancelar</button><button className="button button--primary" disabled={busy || !assigning.usuario_ids.length}>Crear asignación</button></div>
        </form>}
      </Modal>
    </>
  );
}
