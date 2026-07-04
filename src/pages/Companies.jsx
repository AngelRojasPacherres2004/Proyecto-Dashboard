import { useEffect, useMemo, useState } from "react";
import { Building2, Edit3, Mail, Plus, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import {
  ConfirmDialog, EmptyState, Field, Loading, Modal, Notice,
  PageHeader, SearchInput, StatusBadge,
} from "../components/UI";

const blank = {
  alias: "", razon_social: "", ruc: "", sunat_usuario: "", sunat_clave: "",
  regimen_tributario: "", regimen_laboral: "", afpnet_usuario: "", afpnet_clave: "",
  bn_usuario: "", bn_clave: "", bn_cta_detraccion: "", giro_negocio: "",
  estado_contrato: "Activo", fecha_contrato: "", correo_principal: "",
  digio_ruc: "", p_electronico: "",
};

export default function Companies({ refreshReferences }) {
  const [items, setItems] = useState(null);
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState(null);
  const [tab, setTab] = useState("general");
  const [deleting, setDeleting] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const load = () => api("/companies").then(setItems).catch((err) => setNotice({ type: "error", text: err.message }));
  useEffect(() => { load(); }, []);
  const filtered = useMemo(() => (items || []).filter((item) =>
    [item.alias, item.razon_social, item.ruc, item.regimen_tributario].join(" ").toLowerCase().includes(search.toLowerCase()),
  ), [items, search]);
  const openNew = () => { setTab("general"); setEditing({ ...blank }); };
  const openEdit = async (item) => {
    setBusy(true);
    try {
      const detail = await api(`/companies/${item.id}`);
      setTab("general");
      setEditing({ ...blank, ...detail, fecha_contrato: detail.fecha_contrato?.slice(0, 10) || "" });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  const set = (field, value) => setEditing((current) => ({ ...current, [field]: value }));
  const save = async (event) => {
    event.preventDefault(); setBusy(true); setNotice(null);
    try {
      await api(editing.id ? `/companies/${editing.id}` : "/companies", {
        method: editing.id ? "PUT" : "POST", body: editing,
      });
      setEditing(null); await Promise.all([load(), refreshReferences()]);
      setNotice({ type: "success", text: editing.id ? "Empresa actualizada." : "Empresa registrada." });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };
  const remove = async () => {
    setBusy(true);
    try {
      await api(`/companies/${deleting.id}`, { method: "DELETE" });
      setDeleting(null); await Promise.all([load(), refreshReferences()]);
      setNotice({ type: "success", text: "Empresa eliminada." });
    } catch (err) { setNotice({ type: "error", text: err.message }); }
    finally { setBusy(false); }
  };

  return (
    <>
      <PageHeader eyebrow="Directorio" title="Empresas" subtitle="Datos fiscales, contactos y accesos de cada cliente."
        action={<button className="button button--primary" onClick={openNew}><Plus size={18} />Nueva empresa</button>} />
      {notice && <Notice type={notice.type} onClose={() => setNotice(null)}>{notice.text}</Notice>}
      <div className="toolbar"><SearchInput value={search} onChange={setSearch} placeholder="Buscar por razón social, alias o RUC…" /><span>{filtered.length} empresas</span></div>
      {!items ? <Loading /> : filtered.length ? <div className="company-grid">
        {filtered.map((item) => <article className="company-card" key={item.id}>
          <div className="company-card__head">
            <span className="company-logo">{item.alias?.slice(0, 2).toUpperCase()}</span>
            <StatusBadge value={item.estado_contrato} />
          </div>
          <h3>{item.alias}</h3><p>{item.razon_social}</p>
          <dl><div><dt>RUC</dt><dd>{item.ruc}</dd></div><div><dt>Régimen</dt><dd>{item.regimen_tributario || "No indicado"}</dd></div></dl>
          {item.correo_principal && <a href={`mailto:${item.correo_principal}`}><Mail size={15} />{item.correo_principal}</a>}
          <div className="company-card__footer">
            <button onClick={() => openEdit(item)} disabled={busy}><Edit3 size={16} />Editar</button>
            <button className="danger" onClick={() => setDeleting(item)}><Trash2 size={16} /></button>
          </div>
        </article>)}
      </div> : <EmptyState icon={Building2} title="No encontramos empresas" text="Ajusta tu búsqueda o registra un nuevo cliente." />}

      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing?.id ? "Editar empresa" : "Nueva empresa"} subtitle="La información sensible solo es visible para administradores." wide>
        {editing && <form onSubmit={save}>
          <div className="form-tabs">
            <button type="button" className={tab === "general" ? "active" : ""} onClick={() => setTab("general")}>Datos generales</button>
            <button type="button" className={tab === "credentials" ? "active" : ""} onClick={() => setTab("credentials")}>Credenciales</button>
            <button type="button" className={tab === "contact" ? "active" : ""} onClick={() => setTab("contact")}>Contacto y otros</button>
          </div>
          {tab === "general" && <div className="form-grid">
            <Field label="Alias"><input required value={editing.alias} onChange={(e) => set("alias", e.target.value)} /></Field>
            <Field label="RUC"><input required inputMode="numeric" minLength={11} maxLength={11} value={editing.ruc} onChange={(e) => set("ruc", e.target.value.replace(/\D/g, ""))} /></Field>
            <Field label="Razón social" className="span-2"><input required value={editing.razon_social} onChange={(e) => set("razon_social", e.target.value)} /></Field>
            <Field label="Régimen tributario"><select value={editing.regimen_tributario} onChange={(e) => set("regimen_tributario", e.target.value)}><option value="">Seleccionar</option><option>Régimen General</option><option>Régimen MYPE Tributario</option><option>Régimen Especial de Renta</option><option>Nuevo RUS</option></select></Field>
            <Field label="Régimen laboral"><select value={editing.regimen_laboral} onChange={(e) => set("regimen_laboral", e.target.value)}><option value="">Seleccionar</option><option>General</option><option>Microempresa</option><option>Pequeña empresa</option><option>Agrario</option></select></Field>
            <Field label="Estado del contrato"><select value={editing.estado_contrato} onChange={(e) => set("estado_contrato", e.target.value)}><option>Activo</option><option>Inactivo</option><option>Suspendido</option></select></Field>
            <Field label="Fecha de contrato"><input type="date" value={editing.fecha_contrato} onChange={(e) => set("fecha_contrato", e.target.value)} /></Field>
            <Field label="Giro del negocio" className="span-2"><textarea rows="3" value={editing.giro_negocio || ""} onChange={(e) => set("giro_negocio", e.target.value)} /></Field>
          </div>}
          {tab === "credentials" && <div className="form-grid">
            <div className="form-section-title span-2"><strong>SUNAT</strong><span>Acceso SOL de la empresa</span></div>
            <Field label="Usuario SOL"><input autoComplete="off" value={editing.sunat_usuario || ""} onChange={(e) => set("sunat_usuario", e.target.value)} /></Field>
            <Field label="Clave SOL"><input type="password" autoComplete="new-password" value={editing.sunat_clave || ""} onChange={(e) => set("sunat_clave", e.target.value)} /></Field>
            <div className="form-section-title span-2"><strong>AFPnet</strong><span>Credenciales previsionales</span></div>
            <Field label="Usuario AFPnet"><input autoComplete="off" value={editing.afpnet_usuario || ""} onChange={(e) => set("afpnet_usuario", e.target.value)} /></Field>
            <Field label="Clave AFPnet"><input type="password" autoComplete="new-password" value={editing.afpnet_clave || ""} onChange={(e) => set("afpnet_clave", e.target.value)} /></Field>
            <div className="form-section-title span-2"><strong>Banco de la Nación</strong><span>Acceso y cuenta de detracciones</span></div>
            <Field label="Usuario BN"><input value={editing.bn_usuario || ""} onChange={(e) => set("bn_usuario", e.target.value)} /></Field>
            <Field label="Clave BN"><input type="password" value={editing.bn_clave || ""} onChange={(e) => set("bn_clave", e.target.value)} /></Field>
            <Field label="Cuenta de detracciones" className="span-2"><input value={editing.bn_cta_detraccion || ""} onChange={(e) => set("bn_cta_detraccion", e.target.value)} /></Field>
          </div>}
          {tab === "contact" && <div className="form-grid">
            <Field label="Correo principal" className="span-2"><input type="email" value={editing.correo_principal || ""} onChange={(e) => set("correo_principal", e.target.value)} /></Field>
            <Field label="Dígito RUC"><input value={editing.digio_ruc || ""} onChange={(e) => set("digio_ruc", e.target.value)} /></Field>
            <Field label="Padrón electrónico"><input value={editing.p_electronico || ""} onChange={(e) => set("p_electronico", e.target.value)} /></Field>
          </div>}
          <div className="form-actions"><button type="button" className="button button--ghost" onClick={() => setEditing(null)}>Cancelar</button><button className="button button--primary" disabled={busy}>{busy ? "Guardando…" : "Guardar empresa"}</button></div>
        </form>}
      </Modal>
      <ConfirmDialog open={!!deleting} title="Eliminar empresa" message={`Se eliminará “${deleting?.razon_social}”. No será posible si tiene tareas relacionadas.`} onClose={() => setDeleting(null)} onConfirm={remove} busy={busy} />
    </>
  );
}
