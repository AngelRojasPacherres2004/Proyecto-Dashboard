import { useEffect, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Building2, CheckCircle2, Clock3, ListChecks, UsersRound } from "lucide-react";
import { api, formatDate } from "../lib/api";
import { Loading, Notice, PageHeader } from "../components/UI";

const palette = { completada: "#2f9e78", pendiente: "#e3a33b", vencida: "#db6a66" };
const tooltipStyle = { border: "1px solid #e4e8ee", borderRadius: 12, boxShadow: "0 12px 30px rgba(26,38,54,.12)", fontSize: 12 };

function Metric({ icon: Icon, label, value, note, tone }) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <div className="metric-card__top"><span><Icon size={20} /></span><small>{label}</small></div>
      <strong>{value ?? 0}</strong><p>{note}</p>
    </article>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api("/dashboard").then(setData).catch((err) => setError(err.message)); }, []);
  if (error) return <Notice type="error">{error}</Notice>;
  if (!data) return <Loading />;
  const completionTotal = Number(data.summary.completadas) + Number(data.summary.pendientes) + Number(data.summary.vencidas);
  const completionRate = completionTotal ? Math.round((data.summary.completadas / completionTotal) * 100) : 0;

  return (
    <>
      <PageHeader eyebrow="Centro de control" title="Buenos días" subtitle="Una lectura clara de lo que está ocurriendo hoy." />
      <section className="metrics-grid">
        <Metric icon={UsersRound} label="Equipo activo" value={data.summary.usuarios_activos} note="Usuarios habilitados" tone="blue" />
        <Metric icon={Building2} label="Empresas" value={data.summary.empresas_activas} note="Contratos activos" tone="violet" />
        <Metric icon={Clock3} label="Por completar" value={data.summary.pendientes} note="Requieren seguimiento" tone="amber" />
        <Metric icon={CheckCircle2} label="Completadas" value={data.summary.completadas} note={`${completionRate}% de cumplimiento`} tone="green" />
        <Metric icon={ListChecks} label="Vencidas" value={data.summary.vencidas} note="Fuera de fecha" tone="red" />
      </section>

      <section className="dashboard-grid">
        <article className="panel panel--wide">
          <header className="panel__header"><div><h2>Ritmo de cumplimiento</h2><p>Tareas completadas por mes</p></div><span className="panel-tag">Últimos 12 meses</span></header>
          <div className="chart chart--large">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.trend}>
                <defs><linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#477dbe" stopOpacity={.28} /><stop offset="100%" stopColor="#477dbe" stopOpacity={.02} /></linearGradient></defs>
                <CartesianGrid stroke="#edf0f4" vertical={false} />
                <XAxis dataKey="mes" axisLine={false} tickLine={false} tick={{ fill: "#7a8595", fontSize: 11 }} />
                <YAxis axisLine={false} tickLine={false} allowDecimals={false} tick={{ fill: "#7a8595", fontSize: 11 }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="completadas" stroke="#477dbe" strokeWidth={2.5} fill="url(#trendFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </article>
        <article className="panel">
          <header className="panel__header"><div><h2>Estado general</h2><p>Distribución de asignaciones</p></div></header>
          <div className="donut-wrap">
            <ResponsiveContainer width="100%" height={210}>
              <PieChart><Pie data={data.states} dataKey="cantidad" nameKey="estado" innerRadius={60} outerRadius={82} paddingAngle={3}>
                {data.states.map((item) => <Cell key={item.estado} fill={palette[item.estado] || "#8d96a3"} />)}
              </Pie><Tooltip contentStyle={tooltipStyle} /></PieChart>
            </ResponsiveContainer>
            <div className="donut-center"><strong>{completionTotal}</strong><small>Total</small></div>
          </div>
          <div className="chart-legend">{data.states.map((item) => <span key={item.estado}><i style={{ background: palette[item.estado] }} />{item.estado}<strong>{item.cantidad}</strong></span>)}</div>
        </article>
        <article className="panel panel--wide">
          <header className="panel__header"><div><h2>Carga del equipo</h2><p>Asignaciones por colaborador</p></div></header>
          <div className="chart chart--medium">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.workload} barGap={2}>
                <CartesianGrid stroke="#edf0f4" vertical={false} />
                <XAxis dataKey="nombre" axisLine={false} tickLine={false} tick={{ fill: "#7a8595", fontSize: 11 }} />
                <YAxis axisLine={false} tickLine={false} allowDecimals={false} tick={{ fill: "#7a8595", fontSize: 11 }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="completadas" stackId="a" fill="#2f9e78" radius={[0, 0, 4, 4]} />
                <Bar dataKey="pendientes" stackId="a" fill="#e3a33b" />
                <Bar dataKey="vencidas" stackId="a" fill="#db6a66" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
        <article className="panel">
          <header className="panel__header"><div><h2>Próximos vencimientos</h2><p>Los siguientes 15 días</p></div></header>
          <div className="due-list">
            {data.dueSoon.length ? data.dueSoon.slice(0, 6).map((item, index) => (
              <div key={`${item.usuario}-${index}`}>
                <span className={`due-days ${item.dias_restantes <= 3 ? "urgent" : ""}`}>{item.dias_restantes}d</span>
                <div><strong>{item.tarea}</strong><small>{item.empresa} · {item.usuario}</small></div>
                <time>{formatDate(item.fecha_meta, { year: undefined })}</time>
              </div>
            )) : <div className="panel-empty"><CheckCircle2 size={24} /><span>No hay vencimientos cercanos.</span></div>}
          </div>
        </article>
      </section>
    </>
  );
}
