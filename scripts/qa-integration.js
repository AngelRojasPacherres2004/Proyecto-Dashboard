import crypto from "node:crypto";
import pg from "pg";
import jwt from "jsonwebtoken";

process.env.CREDENTIALS_ENCRYPTION_KEY ||= crypto.randomBytes(32).toString("hex");
const { handler } = await import("../netlify/functions/api.js");

const db = new pg.Client({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});
await db.connect();

const created = {
  userId: null,
  companyId: null,
  taskId: null,
  scheduleId: null,
  assignmentIds: new Set(),
};
const results = [];

function check(condition, message) {
  if (!condition) throw new Error(message);
}

async function call(method, path, { body, token, query = {} } = {}) {
  const response = await handler({
    httpMethod: method,
    path: `/api${path}`,
    headers: {
      ...(token ? { cookie: token } : {}),
      "x-forwarded-proto": "http",
      "x-forwarded-for": `qa-${Date.now()}`,
    },
    queryStringParameters: query,
    body: body === undefined ? null : JSON.stringify(body),
  });
  let payload = {};
  try { payload = JSON.parse(response.body || "{}"); } catch { /* empty response */ }
  return { status: response.statusCode, payload, headers: response.headers || {} };
}

async function expect(name, expectedStatus, operation, verify = () => true) {
  const response = await operation();
  check(response.status === expectedStatus,
    `${name}: se esperaba HTTP ${expectedStatus}, se recibió ${response.status}: ${response.payload.error || ""}`);
  check(verify(response.payload, response), `${name}: la respuesta no cumple la condición esperada.`);
  results.push(`✓ ${name}`);
  return response;
}

async function cleanup() {
  try {
    if (created.userId || created.companyId || created.taskId) {
      await db.query("BEGIN");
      if (created.userId) {
        await db.query("DELETE FROM registros_tareas WHERE usuario_id=$1", [created.userId]);
        await db.query("DELETE FROM asignaciones WHERE usuario_id=$1", [created.userId]);
      }
      if (created.companyId) {
        await db.query("DELETE FROM cronograma_pdt WHERE empresa_id=$1", [created.companyId]);
        await db.query("DELETE FROM asignaciones WHERE empresa_id=$1", [created.companyId]);
      }
      if (created.taskId) {
        await db.query("DELETE FROM cronograma_pdt WHERE tarea_id=$1", [created.taskId]);
        await db.query("DELETE FROM asignaciones WHERE tarea_id=$1", [created.taskId]);
        await db.query("DELETE FROM tareas WHERE id=$1", [created.taskId]);
      }
      if (created.companyId) await db.query("DELETE FROM empresas WHERE id=$1", [created.companyId]);
      if (created.userId) await db.query("DELETE FROM usuarios WHERE id=$1", [created.userId]);
      await db.query("COMMIT");
    }
  } catch (error) {
    await db.query("ROLLBACK").catch(() => {});
    console.error("No se pudo completar la limpieza QA:", error);
    throw error;
  }
}

try {
  const setup = await db.query(`
    SELECT
      (SELECT id FROM usuarios WHERE rol='admin' AND estado='activo' ORDER BY id LIMIT 1) admin_id,
      (SELECT id FROM proyectos ORDER BY id LIMIT 1) project_id,
      CURRENT_DATE::text today,
      (CURRENT_DATE-5)::text past_date,
      (CURRENT_DATE+5)::text future_date,
      (CURRENT_DATE+20)::text schedule_date`);
  const context = setup.rows[0];
  check(context.admin_id && context.project_id, "Se necesita un administrador activo y un proyecto.");
  const adminToken = `nexo_session=${jwt.sign(
    { id: context.admin_id, rol: "admin", nombre: "QA Admin" },
    process.env.JWT_SECRET || "nexo-contable-development-secret-change-me",
    { expiresIn: "15m" },
  )}`;
  const stamp = Date.now().toString().slice(-8);
  const username = `qa_${stamp}`;
  const password = `Qa-${stamp}!`;
  const ruc = `209${stamp}`;

  await expect("salud de API y PostgreSQL", 200,
    () => call("GET", "/health"), (body) => body.ok && body.database === "connected");
  await expect("ruta privada sin sesión", 401, () => call("GET", "/dashboard"));
  await expect("sincronización y dashboard", 200,
    () => call("GET", "/dashboard", { token: adminToken }), (body) => body.summary && body.states);
  await expect("validación de contraseña débil", 400,
    () => call("POST", "/users", {
      token: adminToken,
      body: { nom_res: "QA Débil", alias: "QD", usuario: `weak_${stamp}`, password: "123", rol: "trabajador", estado: "activo" },
    }));

  const user = await expect("crear usuario", 201,
    () => call("POST", "/users", {
      token: adminToken,
      body: { nom_res: "Usuario QA Temporal", alias: "QA", usuario: username, password, rol: "trabajador", estado: "activo" },
    }), (body) => body.id && body.usuario === username);
  created.userId = user.payload.id;

  const login = await expect("inicio de sesión real con bcrypt", 200,
    () => call("POST", "/auth/login", { body: { usuario: username, password } }),
    (body, response) => body.user?.id === created.userId && response.headers["Set-Cookie"]);
  const workerToken = login.headers["Set-Cookie"].split(";")[0];
  await expect("permisos: trabajador no administra usuarios", 403,
    () => call("GET", "/users", { token: workerToken }));
  await expect("protección: administrador no se elimina a sí mismo", 400,
    () => call("DELETE", `/users/${context.admin_id}`, { token: adminToken }));

  await expect("actualizar usuario", 200,
    () => call("PUT", `/users/${created.userId}`, {
      token: adminToken,
      body: { nom_res: "Usuario QA Temporal", alias: "QAT", usuario: username, password: "", rol: "trabajador", estado: "activo" },
    }));
  await expect("rechazar usuario duplicado", 409,
    () => call("POST", "/users", {
      token: adminToken,
      body: { nom_res: "Usuario Duplicado", alias: "DUP", usuario: username, password, rol: "trabajador", estado: "activo" },
    }));

  await expect("validación de RUC", 400,
    () => call("POST", "/companies", {
      token: adminToken,
      body: { alias: "QA", razon_social: "Empresa QA", ruc: "123", estado_contrato: "Activo" },
    }));
  const companyPayload = {
    alias: `QA-${stamp}`, razon_social: "Empresa QA Temporal SAC", ruc,
    sunat_usuario: "QA-SOL", sunat_clave: "secreto-qa",
    regimen_tributario: "Régimen General", regimen_laboral: "General",
    afpnet_usuario: "", afpnet_clave: "", bn_usuario: "", bn_clave: "",
    bn_cta_detraccion: "", giro_negocio: "Prueba automatizada",
    estado_contrato: "Activo", fecha_contrato: context.today,
    correo_principal: `qa${stamp}@example.com`, digio_ruc: "", p_electronico: "",
  };
  const company = await expect("crear empresa", 201,
    () => call("POST", "/companies", { token: adminToken, body: companyPayload }),
    (body) => body.id && body.ruc === ruc);
  created.companyId = company.payload.id;
  await expect("cifrar y recuperar credenciales de empresa", 200,
    () => call("GET", `/companies/${created.companyId}`, { token: adminToken }),
    (body) => body.sunat_clave === "secreto-qa" && body.sunat_usuario === "QA-SOL");
  await expect("actualizar empresa", 200,
    () => call("PUT", `/companies/${created.companyId}`, {
      token: adminToken, body: { ...companyPayload, alias: `QAX-${stamp}` },
    }));

  const task = await expect("crear tarea", 201,
    () => call("POST", "/tasks", {
      token: adminToken,
      body: { nombre_tarea: `__QA__ Tarea ${stamp}`, proyecto_id: context.project_id },
    }), (body) => body.id);
  created.taskId = task.payload.id;
  await expect("rechazar tarea duplicada", 409,
    () => call("POST", "/tasks", {
      token: adminToken,
      body: { nombre_tarea: `__QA__ Tarea ${stamp}`, proyecto_id: context.project_id },
    }));
  await expect("actualizar tarea", 200,
    () => call("PUT", `/tasks/${created.taskId}`, {
      token: adminToken,
      body: { nombre_tarea: `__QA__ Tarea actualizada ${stamp}`, proyecto_id: context.project_id },
    }));

  const commonAssignment = {
    usuario_ids: [created.userId], empresa_id: created.companyId,
    tarea_id: created.taskId, peso: 2,
  };
  await expect("validación de peso de asignación", 400,
    () => call("POST", "/assignments", {
      token: adminToken,
      body: { ...commonAssignment, fecha_meta: context.future_date, peso: 0 },
    }));
  const past = await expect("crear tarea pasada como vencida", 201,
    () => call("POST", "/assignments", {
      token: adminToken,
      body: { ...commonAssignment, fecha_meta: context.past_date },
    }), (body) => body.id && body.estado === "vencida");
  created.assignmentIds.add(past.payload.id);
  await expect("tarea vencida visible al trabajador", 200,
    () => call("GET", "/worker/tasks", { token: workerToken }),
    (body) => body.some((item) => item.id === past.payload.id && item.estado === "vencida"));
  await expect("fecha futura de realización rechazada", 400,
    () => call("PUT", `/worker/tasks/${past.payload.id}`, {
      token: workerToken,
      body: { estado: "completada", fecha_realizada: context.schedule_date },
    }));
  await expect("completar tarea vencida y calcular rendimiento bajo", 200,
    () => call("PUT", `/worker/tasks/${past.payload.id}`, {
      token: workerToken,
      body: { estado: "completada", fecha_realizada: context.today },
    }), (body) => body.rendimiento === "BAJO");
  await expect("progreso completado persistido", 200,
    () => call("GET", `/worker/tasks/${past.payload.id}`, { token: workerToken }),
    (body) => body.estado === "completada" && body.rendimiento === "BAJO");
  await expect("reabrir tarea pasada vuelve a vencida y limpia progreso", 200,
    () => call("PUT", `/worker/tasks/${past.payload.id}`, {
      token: workerToken, body: { estado: "pendiente" },
    }));
  await expect("estado vencido restaurado lógicamente", 200,
    () => call("GET", `/worker/tasks/${past.payload.id}`, { token: workerToken }),
    (body) => body.estado === "vencida" && !body.fecha_realizada);

  const future = await expect("crear tarea futura como pendiente", 201,
    () => call("POST", "/assignments", {
      token: adminToken,
      body: { ...commonAssignment, fecha_meta: context.future_date },
    }), (body) => body.id && body.estado === "pendiente");
  created.assignmentIds.add(future.payload.id);
  await expect("rechazar asignación duplicada", 409,
    () => call("POST", "/assignments", {
      token: adminToken,
      body: { ...commonAssignment, fecha_meta: context.future_date },
    }));
  await expect("impedir completado administrativo sin fecha realizada", 400,
    () => call("PUT", `/assignments/${future.payload.id}`, {
      token: adminToken,
      body: { ...commonAssignment, fecha_meta: context.future_date, estado: "completada" },
    }));
  await expect("completar tarea futura con rendimiento óptimo", 200,
    () => call("PUT", `/worker/tasks/${future.payload.id}`, {
      token: workerToken,
      body: { estado: "completada", fecha_realizada: context.today },
    }), (body) => body.rendimiento === "OPTIMO");
  await expect("perfil refleja las tareas completadas", 200,
    () => call("GET", "/profile", { token: workerToken }),
    (body) => body.stats.total >= 2 && body.stats.completadas >= 1 && body.stats.optimas >= 1);

  const scheduleDate = new Date(`${context.schedule_date}T00:00:00Z`);
  const scheduleRow = {
    tarea_id: created.taskId, empresa_id: created.companyId,
    periodo_mes: scheduleDate.getUTCMonth() + 1,
    periodo_anio: scheduleDate.getUTCFullYear(),
    fecha_vencimiento: context.schedule_date,
  };
  await expect("importar cronograma", 200,
    () => call("POST", "/schedule/import", {
      token: adminToken, body: { rows: [scheduleRow] },
    }), (body) => body.inserted === 1);
  const scheduleDb = await db.query(
    "SELECT id FROM cronograma_pdt WHERE empresa_id=$1 AND tarea_id=$2 AND periodo_mes=$3 AND periodo_anio=$4",
    [created.companyId, created.taskId, scheduleRow.periodo_mes, scheduleRow.periodo_anio],
  );
  created.scheduleId = scheduleDb.rows[0].id;
  const scheduledAssignment = await expect("asignar responsable desde cronograma", 201,
    () => call("POST", `/schedule/${created.scheduleId}/assign`, {
      token: adminToken, body: { usuario_ids: [created.userId], peso: 3 },
    }), (body) => body.assignmentId);
  created.assignmentIds.add(scheduledAssignment.payload.assignmentId);
  await expect("impedir asignar dos veces el mismo vencimiento", 409,
    () => call("POST", `/schedule/${created.scheduleId}/assign`, {
      token: adminToken, body: { usuario_ids: [created.userId], peso: 3 },
    }));
  await expect("cronograma figura como asignado", 200,
    () => call("GET", "/schedule", {
      token: adminToken,
      query: { month: String(scheduleRow.periodo_mes), year: String(scheduleRow.periodo_anio) },
    }), (body) => body.some((row) => Number(row.id) === Number(created.scheduleId) && row.asignado));

  for (const assignmentId of created.assignmentIds) {
    await expect(`eliminar asignación QA #${assignmentId}`, 200,
      () => call("DELETE", `/assignments/${assignmentId}`, { token: adminToken }));
  }
  created.assignmentIds.clear();
  await db.query("DELETE FROM cronograma_pdt WHERE id=$1", [created.scheduleId]);
  created.scheduleId = null;
  await expect("eliminar tarea QA", 200,
    () => call("DELETE", `/tasks/${created.taskId}`, { token: adminToken }));
  created.taskId = null;
  await expect("eliminar empresa QA", 200,
    () => call("DELETE", `/companies/${created.companyId}`, { token: adminToken }));
  created.companyId = null;
  await expect("eliminar usuario QA", 200,
    () => call("DELETE", `/users/${created.userId}`, { token: adminToken }));
  created.userId = null;

  console.log(results.join("\n"));
  console.log(`\n${results.length} pruebas integrales superadas.`);
} finally {
  await cleanup();
  await db.end();
}
