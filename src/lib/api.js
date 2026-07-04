export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: "include",
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
    body: options.body && typeof options.body !== "string"
      ? JSON.stringify(options.body)
      : options.body,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.error || "No se pudo completar la operación.");
    error.status = response.status;
    throw error;
  }
  return payload;
}

export const formatDate = (value, options = {}) => {
  if (!value) return "—";
  const date = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  return new Intl.DateTimeFormat("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    ...options,
  }).format(date);
};

export const todayISO = () => {
  const now = new Date();
  const offset = now.getTimezoneOffset();
  return new Date(now.getTime() - offset * 60_000).toISOString().slice(0, 10);
};
