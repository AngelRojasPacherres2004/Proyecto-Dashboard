import { useEffect, useState } from "react";
import { CheckCircle2, Clock3, Medal, UserCircle2 } from "lucide-react";
import { api, formatDate } from "../lib/api";
import { Loading, Notice, PageHeader, StatusBadge } from "../components/UI";

export default function Profile() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api("/profile").then(setData).catch((err) => setError(err.message)); }, []);
  if (error) return <Notice type="error">{error}</Notice>;
  if (!data) return <Loading />;
  const { profile, stats } = data;
  const rate = stats.total ? Math.round((stats.completadas / stats.total) * 100) : 0;
  return (
    <>
      <PageHeader eyebrow="Cuenta" title="Mi perfil" subtitle="Tu información y una fotografía de tu desempeño." />
      <section className="profile-hero">
        <span className="profile-avatar">{profile.alias?.charAt(0) || "U"}</span>
        <div><StatusBadge value={profile.estado} /><h2>{profile.nom_res}</h2><p>@{profile.usuario} · {profile.alias}</p></div>
        <div className="profile-completion"><strong>{rate}%</strong><span>Cumplimiento</span></div>
      </section>
      <section className="worker-summary">
        <div><span className="worker-summary__icon blue"><UserCircle2 /></span><div><small>Tareas asignadas</small><strong>{stats.total}</strong></div></div>
        <div><span className="worker-summary__icon green"><CheckCircle2 /></span><div><small>Completadas</small><strong>{stats.completadas}</strong></div></div>
        <div><span className="worker-summary__icon amber"><Clock3 /></span><div><small>Pendientes</small><strong>{stats.pendientes}</strong></div></div>
        <div><span className="worker-summary__icon violet"><Medal /></span><div><small>Rendimiento óptimo</small><strong>{stats.optimas}</strong></div></div>
      </section>
      <section className="profile-details panel">
        <header className="panel__header"><div><h2>Información profesional</h2><p>Datos administrados por tu organización</p></div></header>
        <dl>
          <div><dt>Nombre completo</dt><dd>{profile.nom_res}</dd></div>
          <div><dt>Alias</dt><dd>{profile.alias}</dd></div>
          <div><dt>Área</dt><dd>{profile.nombre_area || "Sin asignar"}</dd></div>
          <div><dt>Subárea</dt><dd>{profile.nombre_subarea || "Sin asignar"}</dd></div>
          <div><dt>Rol</dt><dd>{profile.rol}</dd></div>
          <div><dt>Miembro desde</dt><dd>{formatDate(profile.fecha_creacion)}</dd></div>
        </dl>
      </section>
    </>
  );
}
