import {
  BarChart3, Building2, CalendarDays, CheckSquare2, ClipboardList,
  LogOut, Menu, PanelLeftClose, UserCircle2, Users, X,
} from "lucide-react";
import { useEffect, useState } from "react";

const adminItems = [
  { id: "dashboard", label: "Resumen", icon: BarChart3 },
  { id: "assignments", label: "Asignaciones", icon: ClipboardList },
  { id: "schedule", label: "Cronograma", icon: CalendarDays },
  { id: "companies", label: "Empresas", icon: Building2 },
  { id: "users", label: "Equipo", icon: Users },
  { id: "tasks", label: "Catálogo de tareas", icon: CheckSquare2 },
];
const workerItems = [
  { id: "my-tasks", label: "Mis tareas", icon: ClipboardList },
  { id: "profile", label: "Mi perfil", icon: UserCircle2 },
];

export default function Layout({ user, page, onNavigate, onLogout, children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [compact, setCompact] = useState(false);
  const items = user.rol === "admin" ? adminItems : workerItems;
  useEffect(() => setMobileOpen(false), [page]);

  return (
    <div className={`app-shell ${compact ? "app-shell--compact" : ""}`}>
      {mobileOpen && <button className="sidebar-overlay" onClick={() => setMobileOpen(false)} aria-label="Cerrar menú" />}
      <aside className={`sidebar ${mobileOpen ? "sidebar--open" : ""}`}>
        <div className="brand">
          <span className="brand__mark">N</span>
          <div><strong>Nexo</strong><small>Gestión contable</small></div>
          <button className="sidebar-mobile-close" onClick={() => setMobileOpen(false)}><X size={20} /></button>
        </div>
        <nav>
          <span className="nav-label">Espacio de trabajo</span>
          {items.map(({ id, label, icon: Icon }) => (
            <button key={id} className={page === id ? "active" : ""} onClick={() => onNavigate(id)} title={label}>
              <Icon size={19} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar__footer">
          <div className="user-chip">
            <span>{(user.nombre || user.alias || "U").charAt(0).toUpperCase()}</span>
            <div><strong>{user.alias || user.nombre}</strong><small>{user.rol === "admin" ? "Administrador" : "Colaborador"}</small></div>
          </div>
          <button className="logout-button" onClick={onLogout} title="Cerrar sesión"><LogOut size={18} /><span>Salir</span></button>
        </div>
      </aside>
      <main className="workspace">
        <div className="mobile-topbar">
          <button onClick={() => setMobileOpen(true)}><Menu /></button>
          <span className="brand__mark brand__mark--small">N</span>
          <strong>Nexo</strong>
        </div>
        <button className="compact-toggle" onClick={() => setCompact(!compact)} title="Contraer menú"><PanelLeftClose size={18} /></button>
        <div className="workspace__content">{children}</div>
      </main>
    </div>
  );
}
