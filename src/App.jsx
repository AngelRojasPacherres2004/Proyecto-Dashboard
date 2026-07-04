import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { api } from "./lib/api";
import Layout from "./components/Layout";
import { Loading } from "./components/UI";

const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Users = lazy(() => import("./pages/Users"));
const Companies = lazy(() => import("./pages/Companies"));
const Tasks = lazy(() => import("./pages/Tasks"));
const Assignments = lazy(() => import("./pages/Assignments"));
const Schedule = lazy(() => import("./pages/Schedule"));
const WorkerTasks = lazy(() => import("./pages/WorkerTasks"));
const Profile = lazy(() => import("./pages/Profile"));

const pageForRole = (role) => role === "admin" ? "dashboard" : "my-tasks";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [page, setPage] = useState("dashboard");
  const [references, setReferences] = useState(null);

  useEffect(() => {
    api("/auth/me")
      .then(({ user: account }) => {
        setUser(account);
        setPage(pageForRole(account.rol));
      })
      .catch(() => setUser(null))
      .finally(() => setChecking(false));
  }, []);

  const loadReferences = useCallback(async (force = false) => {
    if (!user || user.rol !== "admin") return null;
    if (references && !force) return references;
    const data = await api("/references");
    setReferences(data);
    return data;
  }, [references, user]);

  useEffect(() => {
    if (user?.rol === "admin") loadReferences().catch(() => {});
  }, [user, loadReferences]);

  const login = (account) => {
    setUser(account);
    setPage(pageForRole(account.rol));
  };
  const logout = async () => {
    await api("/auth/logout", { method: "POST" }).catch(() => {});
    setUser(null);
    setReferences(null);
  };

  if (checking) return <div className="splash"><Loading label="Preparando tu espacio…" /></div>;
  if (!user) return <Suspense fallback={<div className="splash"><Loading /></div>}><Login onLogin={login} /></Suspense>;

  const props = { references, refreshReferences: () => loadReferences(true) };
  const content = {
    dashboard: <Dashboard />,
    users: <Users {...props} />,
    companies: <Companies {...props} />,
    tasks: <Tasks {...props} />,
    assignments: <Assignments {...props} />,
    schedule: <Schedule {...props} />,
    "my-tasks": <WorkerTasks />,
    profile: <Profile />,
  }[page] || <Dashboard />;

  return <Layout user={user} page={page} onNavigate={setPage} onLogout={logout}>
    <Suspense fallback={<Loading />}>{content}</Suspense>
  </Layout>;
}
