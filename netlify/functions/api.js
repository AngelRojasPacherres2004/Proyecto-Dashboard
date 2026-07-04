import { Pool } from "pg";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { parse as parseCookie, serialize as serializeCookie } from "cookie";
import crypto from "node:crypto";

let activePool;
function getPool() {
  if (!activePool) {
    activePool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: process.env.DATABASE_URL?.includes("localhost")
        ? false
        : { rejectUnauthorized: false },
      max: 6,
      idleTimeoutMillis: 20_000,
      connectionTimeoutMillis: 10_000,
    });
  }
  return activePool;
}
const pool = {
  query: (...args) => getPool().query(...args),
  connect: (...args) => getPool().connect(...args),
};

const companyFields = [
  "alias", "razon_social", "ruc", "sunat_usuario", "sunat_clave",
  "regimen_tributario", "regimen_laboral", "afpnet_usuario", "afpnet_clave",
  "bn_usuario", "bn_clave", "bn_cta_detraccion", "giro_negocio",
  "estado_contrato", "fecha_contrato", "correo_principal", "digio_ruc",
  "p_electronico",
];
const secretCompanyFields = new Set([
  "sunat_usuario", "sunat_clave", "afpnet_usuario", "afpnet_clave",
  "bn_usuario", "bn_clave",
]);

const headers = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
};
const loginAttempts = new Map();
const assignmentStates = new Set(["pendiente", "completada", "vencida"]);

function json(statusCode, body, extraHeaders = {}) {
  return { statusCode, headers: { ...headers, ...extraHeaders }, body: JSON.stringify(body) };
}

function normalizePath(event) {
  return event.path
    .replace(/^\/\.netlify\/functions\/api/, "")
    .replace(/^\/api/, "")
    .replace(/\/+$/, "") || "/";
}

function bodyOf(event) {
  try {
    return event.body ? JSON.parse(event.body) : {};
  } catch {
    throw Object.assign(new Error("El cuerpo de la solicitud no es JSON válido."), { status: 400 });
  }
}

function requireFields(data, fields) {
  const missing = fields.filter((key) => data[key] === undefined || data[key] === null || data[key] === "");
  if (missing.length) {
    throw Object.assign(new Error(`Completa los campos obligatorios: ${missing.join(", ")}.`), { status: 400 });
  }
}

function requireAssignmentState(value) {
  if (!assignmentStates.has(value)) {
    throw Object.assign(new Error("El estado de la asignación no es válido."), { status: 400 });
  }
}

function jwtSecret() {
  const secret = process.env.JWT_SECRET;
  if (secret) return secret;
  if (process.env.CONTEXT === "production") {
    throw Object.assign(new Error("Falta configurar JWT_SECRET en Netlify."), { status: 500 });
  }
  return "nexo-contable-development-secret-change-me";
}

function sessionCookie(token, event) {
  const isProduction = process.env.CONTEXT === "production" || event.headers["x-forwarded-proto"] === "https";
  return serializeCookie("nexo_session", token, {
    httpOnly: true,
    secure: isProduction,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 10,
  });
}

function clearSessionCookie(event) {
  const isProduction = process.env.CONTEXT === "production" || event.headers["x-forwarded-proto"] === "https";
  return serializeCookie("nexo_session", "", {
    httpOnly: true,
    secure: isProduction,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
}

function currentUser(event) {
  const cookies = parseCookie(event.headers.cookie || "");
  const bearer = event.headers.authorization?.replace(/^Bearer\s+/i, "");
  const token = cookies.nexo_session || bearer;
  if (!token) return null;
  try {
    return jwt.verify(token, jwtSecret());
  } catch {
    return null;
  }
}

function ensureAuth(event, role) {
  const user = currentUser(event);
  if (!user) throw Object.assign(new Error("Tu sesión expiró. Inicia sesión nuevamente."), { status: 401 });
  if (role && user.rol !== role) {
    throw Object.assign(new Error("No tienes permisos para realizar esta acción."), { status: 403 });
  }
  return user;
}

function encryptionKey() {
  const value = process.env.CREDENTIALS_ENCRYPTION_KEY;
  return value && /^[a-fA-F0-9]{64}$/.test(value) ? Buffer.from(value, "hex") : null;
}

function encryptValue(value) {
  if (!value || String(value).startsWith("enc:")) return value || "";
  const key = encryptionKey();
  if (!key) {
    if (["production", "deploy-preview", "branch-deploy"].includes(process.env.CONTEXT)) {
      throw Object.assign(new Error("Falta configurar CREDENTIALS_ENCRYPTION_KEY en Netlify."), { status: 500 });
    }
    return value;
  }
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const encrypted = Buffer.concat([cipher.update(String(value), "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return `enc:${iv.toString("base64")}:${tag.toString("base64")}:${encrypted.toString("base64")}`;
}

function decryptValue(value) {
  if (!value || !String(value).startsWith("enc:")) return value || "";
  const key = encryptionKey();
  if (!key) return "";
  try {
    const [, iv, tag, encrypted] = value.split(":");
    const decipher = crypto.createDecipheriv("aes-256-gcm", key, Buffer.from(iv, "base64"));
    decipher.setAuthTag(Buffer.from(tag, "base64"));
    return Buffer.concat([
      decipher.update(Buffer.from(encrypted, "base64")),
      decipher.final(),
    ]).toString("utf8");
  } catch {
    return "";
  }
}

async function login(event) {
  const clientIp = event.headers["x-nf-client-connection-ip"]
    || event.headers["x-forwarded-for"]?.split(",")[0]?.trim()
    || "local";
  const attempt = loginAttempts.get(clientIp);
  if (attempt?.blockedUntil > Date.now()) {
    return json(429, { error: "Demasiados intentos. Espera unos minutos antes de volver a intentar." });
  }
  const { usuario, password } = bodyOf(event);
  requireFields({ usuario, password }, ["usuario", "password"]);
  const result = await pool.query(
    `SELECT id, nom_res, alias, usuario, password, rol, estado
     FROM usuarios WHERE LOWER(usuario)=LOWER($1) LIMIT 1`,
    [String(usuario).trim()],
  );
  const account = result.rows[0];
  if (!account || account.estado !== "activo") {
    const count = (attempt?.count || 0) + 1;
    loginAttempts.set(clientIp, { count, blockedUntil: count >= 5 ? Date.now() + 15 * 60_000 : 0 });
    return json(401, { error: "Usuario o contraseña incorrectos." });
  }
  const isHash = /^\$2[aby]\$/.test(account.password);
  const storedPassword = Buffer.from(String(account.password));
  const suppliedPassword = Buffer.from(String(password));
  const valid = isHash
    ? await bcrypt.compare(String(password), account.password)
    : storedPassword.length === suppliedPassword.length
      && crypto.timingSafeEqual(storedPassword, suppliedPassword);
  if (!valid) {
    const count = (attempt?.count || 0) + 1;
    loginAttempts.set(clientIp, { count, blockedUntil: count >= 5 ? Date.now() + 15 * 60_000 : 0 });
    return json(401, { error: "Usuario o contraseña incorrectos." });
  }

  loginAttempts.delete(clientIp);
  if (!isHash) {
    const hash = await bcrypt.hash(String(password), 12);
    await pool.query("UPDATE usuarios SET password=$1 WHERE id=$2", [hash, account.id]);
  }
  const user = {
    id: account.id,
    nombre: account.nom_res,
    alias: account.alias,
    usuario: account.usuario,
    rol: account.rol,
  };
  const token = jwt.sign(user, jwtSecret(), { expiresIn: "10h" });
  return json(200, { user }, { "Set-Cookie": sessionCookie(token, event) });
}

async function getDashboard() {
  const [summary, states, workload, companies, trend, regimes, projects, dueSoon] = await Promise.all([
    pool.query(`
      SELECT
        (SELECT COUNT(*)::int FROM usuarios WHERE estado='activo') usuarios_activos,
        (SELECT COUNT(*)::int FROM empresas WHERE estado_contrato='Activo') empresas_activas,
        (SELECT COUNT(*)::int FROM asignaciones WHERE estado='pendiente') pendientes,
        (SELECT COUNT(*)::int FROM asignaciones WHERE estado='completada') completadas,
        (SELECT COUNT(*)::int FROM asignaciones WHERE estado='vencida') vencidas`),
    pool.query("SELECT estado, COUNT(*)::int cantidad FROM asignaciones GROUP BY estado ORDER BY cantidad DESC"),
    pool.query(`
      SELECT u.alias nombre, COUNT(*)::int total,
        COUNT(*) FILTER (WHERE a.estado='pendiente')::int pendientes,
        COUNT(*) FILTER (WHERE a.estado='completada')::int completadas,
        COUNT(*) FILTER (WHERE a.estado='vencida')::int vencidas
      FROM asignaciones a JOIN usuarios u ON u.id=a.usuario_id
      GROUP BY u.id, u.alias ORDER BY total DESC LIMIT 8`),
    pool.query(`
      SELECT e.alias empresa, COUNT(*)::int total,
        COUNT(*) FILTER (WHERE a.estado='completada')::int completadas,
        COUNT(*) FILTER (WHERE a.estado='pendiente')::int pendientes
      FROM asignaciones a JOIN empresas e ON e.id=a.empresa_id
      GROUP BY e.id, e.alias ORDER BY total DESC LIMIT 8`),
    pool.query(`
      SELECT TO_CHAR(fecha_meta,'YYYY-MM') mes, COUNT(*)::int completadas
      FROM asignaciones WHERE estado='completada'
      GROUP BY 1 ORDER BY 1 DESC LIMIT 12`),
    pool.query(`
      SELECT COALESCE(regimen_tributario,'Sin régimen') regimen, COUNT(*)::int cantidad
      FROM empresas WHERE estado_contrato='Activo' GROUP BY 1 ORDER BY cantidad DESC`),
    pool.query(`
      SELECT p.nombre_proyecto proyecto, a.estado, COUNT(*)::int cantidad
      FROM asignaciones a JOIN tareas t ON t.id=a.tarea_id
      JOIN proyectos p ON p.id=t.proyecto_id
      GROUP BY p.nombre_proyecto,a.estado ORDER BY proyecto`),
    pool.query(`
      SELECT u.alias usuario, e.alias empresa, t.nombre_tarea tarea, a.fecha_meta,
        (a.fecha_meta-CURRENT_DATE)::int dias_restantes
      FROM asignaciones a JOIN usuarios u ON u.id=a.usuario_id
      JOIN empresas e ON e.id=a.empresa_id JOIN tareas t ON t.id=a.tarea_id
      WHERE a.estado='pendiente' AND a.fecha_meta BETWEEN CURRENT_DATE AND CURRENT_DATE+15
      ORDER BY a.fecha_meta LIMIT 20`),
  ]);
  return {
    summary: summary.rows[0],
    states: states.rows,
    workload: workload.rows,
    companies: companies.rows,
    trend: trend.rows.reverse(),
    regimes: regimes.rows,
    projects: projects.rows,
    dueSoon: dueSoon.rows,
  };
}

async function getReferences() {
  const [areas, subareas, projects, users, companies, tasks] = await Promise.all([
    pool.query("SELECT id,nombre_area FROM areas ORDER BY nombre_area"),
    pool.query("SELECT id,area_id,nombre_subarea FROM subareas ORDER BY nombre_subarea"),
    pool.query("SELECT id,nombre_proyecto FROM proyectos ORDER BY nombre_proyecto"),
    pool.query("SELECT id,nom_res,alias FROM usuarios WHERE estado='activo' AND rol='trabajador' ORDER BY nom_res"),
    pool.query("SELECT id,razon_social,alias,ruc FROM empresas WHERE estado_contrato='Activo' ORDER BY razon_social"),
    pool.query(`SELECT t.id,t.nombre_tarea,t.proyecto_id,p.nombre_proyecto
      FROM tareas t JOIN proyectos p ON p.id=t.proyecto_id
      ORDER BY p.nombre_proyecto,t.nombre_tarea`),
  ]);
  return {
    areas: areas.rows,
    subareas: subareas.rows,
    projects: projects.rows,
    users: users.rows,
    companies: companies.rows,
    tasks: tasks.rows,
  };
}

async function listUsers() {
  const { rows } = await pool.query(`
    SELECT u.id,u.nom_res,u.alias,u.usuario,u.rol,u.estado,u.fecha_creacion,
      s.id subarea_id,s.nombre_subarea,s.area_id,a.nombre_area
    FROM usuarios u LEFT JOIN subareas s ON s.id=u.subarea_id
    LEFT JOIN areas a ON a.id=s.area_id ORDER BY u.id`);
  return rows;
}

async function createUser(event) {
  const data = bodyOf(event);
  requireFields(data, ["nom_res", "alias", "usuario", "password", "rol", "estado"]);
  const password = await bcrypt.hash(String(data.password), 12);
  const { rows } = await pool.query(
    `INSERT INTO usuarios (nom_res,alias,usuario,password,subarea_id,rol,estado)
     VALUES ($1,$2,$3,$4,$5,$6,$7)
     RETURNING id,nom_res,alias,usuario,rol,estado,subarea_id`,
    [data.nom_res.trim(), data.alias.trim(), data.usuario.trim(), password,
      data.subarea_id || null, data.rol, data.estado],
  );
  return rows[0];
}

async function updateUser(event, id) {
  const data = bodyOf(event);
  requireFields(data, ["nom_res", "alias", "usuario", "rol", "estado"]);
  const values = [data.nom_res.trim(), data.alias.trim(), data.usuario.trim(),
    data.subarea_id || null, data.rol, data.estado, id];
  let query = `UPDATE usuarios SET nom_res=$1,alias=$2,usuario=$3,subarea_id=$4,rol=$5,estado=$6 WHERE id=$7`;
  if (data.password) {
    values.push(await bcrypt.hash(String(data.password), 12));
    query = `UPDATE usuarios SET nom_res=$1,alias=$2,usuario=$3,subarea_id=$4,rol=$5,estado=$6,password=$8 WHERE id=$7`;
  }
  const result = await pool.query(query, values);
  if (!result.rowCount) throw Object.assign(new Error("Usuario no encontrado."), { status: 404 });
}

async function listCompanies() {
  const { rows } = await pool.query(`
    SELECT id,alias,razon_social,ruc,regimen_tributario,regimen_laboral,
      estado_contrato,correo_principal,giro_negocio,fecha_contrato,fecha_registro
    FROM empresas ORDER BY razon_social`);
  return rows;
}

async function companyDetail(id) {
  const { rows } = await pool.query("SELECT * FROM empresas WHERE id=$1", [id]);
  if (!rows[0]) throw Object.assign(new Error("Empresa no encontrada."), { status: 404 });
  for (const field of secretCompanyFields) rows[0][field] = decryptValue(rows[0][field]);
  return rows[0];
}

function companyValues(data) {
  return companyFields.map((field) => {
    const value = data[field] ?? null;
    return secretCompanyFields.has(field) ? encryptValue(value) : value || null;
  });
}

async function createCompany(event) {
  const data = bodyOf(event);
  requireFields(data, ["alias", "razon_social", "ruc", "estado_contrato"]);
  const columns = companyFields.join(",");
  const placeholders = companyFields.map((_, i) => `$${i + 1}`).join(",");
  const { rows } = await pool.query(
    `INSERT INTO empresas (${columns}) VALUES (${placeholders})
     RETURNING id,alias,razon_social,ruc,estado_contrato`,
    companyValues(data),
  );
  return rows[0];
}

async function updateCompany(event, id) {
  const data = bodyOf(event);
  requireFields(data, ["alias", "razon_social", "ruc", "estado_contrato"]);
  const assignments = companyFields.map((field, i) => `${field}=$${i + 1}`).join(",");
  const result = await pool.query(
    `UPDATE empresas SET ${assignments} WHERE id=$${companyFields.length + 1}`,
    [...companyValues(data), id],
  );
  if (!result.rowCount) throw Object.assign(new Error("Empresa no encontrada."), { status: 404 });
}

async function listTasks() {
  const { rows } = await pool.query(`
    SELECT t.id,t.nombre_tarea,t.proyecto_id,p.nombre_proyecto
    FROM tareas t JOIN proyectos p ON p.id=t.proyecto_id
    ORDER BY p.nombre_proyecto,t.nombre_tarea`);
  return rows;
}

async function createTask(event) {
  const data = bodyOf(event);
  requireFields(data, ["nombre_tarea", "proyecto_id"]);
  const { rows } = await pool.query(
    "INSERT INTO tareas (nombre_tarea,proyecto_id) VALUES ($1,$2) RETURNING *",
    [data.nombre_tarea.trim(), data.proyecto_id],
  );
  return rows[0];
}

async function updateTask(event, id) {
  const data = bodyOf(event);
  requireFields(data, ["nombre_tarea", "proyecto_id"]);
  const result = await pool.query(
    "UPDATE tareas SET nombre_tarea=$1,proyecto_id=$2 WHERE id=$3",
    [data.nombre_tarea.trim(), data.proyecto_id, id],
  );
  if (!result.rowCount) throw Object.assign(new Error("Tarea no encontrada."), { status: 404 });
}

async function listAssignments(event) {
  const query = event.queryStringParameters || {};
  const where = [];
  const params = [];
  if (query.month && query.year) {
    params.push(query.month, query.year);
    where.push(`EXTRACT(MONTH FROM a.fecha_meta)=$${params.length - 1} AND EXTRACT(YEAR FROM a.fecha_meta)=$${params.length}`);
  }
  if (query.status) {
    params.push(query.status);
    where.push(`a.estado=$${params.length}`);
  }
  const { rows } = await pool.query(`
    SELECT a.id,a.usuario_id,u.nom_res trabajador,u.alias,e.razon_social empresa,
      e.id empresa_id,t.nombre_tarea tarea,t.id tarea_id,p.nombre_proyecto proyecto,
      a.fecha_meta,a.estado,a.fecha_creacion,a.peso,
      (SELECT rt.fecha_realizada FROM registros_tareas rt
       WHERE rt.asignacion_id=a.id AND rt.usuario_id=a.usuario_id
       ORDER BY rt.id DESC LIMIT 1) fecha_realizada
    FROM asignaciones a JOIN usuarios u ON u.id=a.usuario_id
    JOIN empresas e ON e.id=a.empresa_id JOIN tareas t ON t.id=a.tarea_id
    JOIN proyectos p ON p.id=t.proyecto_id
    ${where.length ? `WHERE ${where.join(" AND ")}` : ""}
    ORDER BY a.fecha_meta DESC,a.id DESC,a.usuario_id`, params);
  const groups = new Map();
  for (const row of rows) {
    if (!groups.has(row.id)) groups.set(row.id, {
      id: row.id, empresa: row.empresa, empresa_id: row.empresa_id,
      tarea: row.tarea, tarea_id: row.tarea_id, proyecto: row.proyecto,
      fecha_meta: row.fecha_meta, estado: row.estado,
      fecha_creacion: row.fecha_creacion, peso: row.peso, trabajadores: [],
    });
    groups.get(row.id).trabajadores.push({
      usuario_id: row.usuario_id, trabajador: row.trabajador,
      alias: row.alias, fecha_realizada: row.fecha_realizada,
    });
  }
  return [...groups.values()];
}

async function createAssignment(event) {
  const data = bodyOf(event);
  requireFields(data, ["usuario_ids", "empresa_id", "tarea_id", "fecha_meta"]);
  if (!Array.isArray(data.usuario_ids) || !data.usuario_ids.length) {
    throw Object.assign(new Error("Selecciona al menos un trabajador."), { status: 400 });
  }
  requireAssignmentState(data.estado || "pendiente");
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const next = await client.query("SELECT get_next_asignacion_id() nuevo_id");
    const id = next.rows[0].nuevo_id;
    for (const userId of [...new Set(data.usuario_ids)]) {
      await client.query(
        `INSERT INTO asignaciones (id,usuario_id,empresa_id,tarea_id,fecha_meta,estado,peso)
         OVERRIDING SYSTEM VALUE VALUES ($1,$2,$3,$4,$5,$6,$7)`,
        [id, userId, data.empresa_id, data.tarea_id, data.fecha_meta, data.estado || "pendiente", data.peso || 1],
      );
    }
    await client.query("COMMIT");
    return { id };
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

async function updateAssignment(event, id) {
  const data = bodyOf(event);
  requireFields(data, ["usuario_ids", "empresa_id", "tarea_id", "fecha_meta", "estado"]);
  const desired = [...new Set(data.usuario_ids.map(Number))];
  requireAssignmentState(data.estado);
  if (!desired.length) throw Object.assign(new Error("Selecciona al menos un trabajador."), { status: 400 });
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const current = await client.query("SELECT usuario_id FROM asignaciones WHERE id=$1", [id]);
    if (!current.rowCount) throw Object.assign(new Error("Asignación no encontrada."), { status: 404 });
    const existing = current.rows.map((row) => Number(row.usuario_id));
    const remove = existing.filter((userId) => !desired.includes(userId));
    const add = desired.filter((userId) => !existing.includes(userId));
    await client.query(
      "UPDATE asignaciones SET empresa_id=$1,tarea_id=$2,fecha_meta=$3,estado=$4,peso=$5 WHERE id=$6",
      [data.empresa_id, data.tarea_id, data.fecha_meta, data.estado, data.peso || 1, id],
    );
    if (remove.length) await client.query("DELETE FROM asignaciones WHERE id=$1 AND usuario_id=ANY($2::int[])", [id, remove]);
    for (const userId of add) {
      await client.query(
        `INSERT INTO asignaciones (id,usuario_id,empresa_id,tarea_id,fecha_meta,estado,peso)
         OVERRIDING SYSTEM VALUE VALUES ($1,$2,$3,$4,$5,$6,$7)`,
        [id, userId, data.empresa_id, data.tarea_id, data.fecha_meta, data.estado, data.peso || 1],
      );
    }
    await client.query("COMMIT");
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

async function deleteAssignment(id) {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const ref = await client.query(
      "SELECT empresa_id,tarea_id,fecha_meta FROM asignaciones WHERE id=$1 LIMIT 1", [id],
    );
    if (!ref.rowCount) throw Object.assign(new Error("Asignación no encontrada."), { status: 404 });
    await client.query("DELETE FROM asignaciones WHERE id=$1", [id]);
    const item = ref.rows[0];
    const another = await client.query(
      "SELECT 1 FROM asignaciones WHERE empresa_id=$1 AND tarea_id=$2 AND fecha_meta=$3 LIMIT 1",
      [item.empresa_id, item.tarea_id, item.fecha_meta],
    );
    if (!another.rowCount) {
      await client.query(
        "UPDATE cronograma_pdt SET asignado=false WHERE empresa_id=$1 AND tarea_id=$2 AND fecha_vencimiento=$3",
        [item.empresa_id, item.tarea_id, item.fecha_meta],
      );
    }
    await client.query("COMMIT");
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

const monthTokens = {
  ene: 1, feb: 2, mar: 3, abr: 4, may: 5, jun: 6,
  jul: 7, ago: 8, set: 9, sep: 9, oct: 10, nov: 11, dic: 12,
};
const scheduleGroups = ["0", "1", "23", "45", "67", "89"];

function dateISO(date) {
  return date.toISOString().slice(0, 10);
}

function parsePeriod(text, forcedYear) {
  const normalized = text.toLowerCase().replace(/\*/g, "").trim();
  const match = normalized.match(/\b(ene(?:ro)?|feb(?:rero)?|mar(?:zo)?|abr(?:il)?|may(?:o)?|jun(?:io)?|jul(?:io)?|ago(?:sto)?|set(?:iembre)?|sep(?:tiembre)?|oct(?:ubre)?|nov(?:iembre)?|dic(?:iembre)?)(?:\s*[-/]\s*|\s+)?(\d{2,4})?\b/i);
  if (!match) return null;
  const month = monthTokens[match[1].slice(0, 3).toLowerCase()];
  const rawYear = match[2] ? Number(match[2]) : forcedYear;
  return { month, year: rawYear < 100 ? 2000 + rawYear : rawYear };
}

function parseDates(text, fallbackYear) {
  const dates = [];
  const regex = /\b(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|set|sep|oct|nov|dic)[a-záéíóúñ.]*\s*(\d{2,4})?\b/gi;
  for (const match of text.matchAll(regex)) {
    const day = Number(match[1]);
    const month = monthTokens[match[2].slice(0, 3).toLowerCase()];
    let year = match[3] ? Number(match[3]) : fallbackYear;
    if (year < 100) year += 2000;
    const date = new Date(Date.UTC(year, month - 1, day));
    if (date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day) {
      dates.push(dateISO(date));
    }
  }
  return dates;
}

async function extractScheduleFromPdf(buffer, forcedYear) {
  const { getDocument } = await import("pdfjs-dist/legacy/build/pdf.mjs");
  const loadingTask = getDocument({
    data: new Uint8Array(buffer),
    disableWorker: true,
    useSystemFonts: true,
  });
  const document = await loadingTask.promise;
  const schedule = new Map();

  for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
    const page = await document.getPage(pageNumber);
    const content = await page.getTextContent();
    const visualRows = [];
    for (const item of content.items) {
      const text = item.str?.replace(/\s+/g, " ").trim();
      if (!text) continue;
      const x = item.transform?.[4] || 0;
      const y = item.transform?.[5] || 0;
      let row = visualRows.find((candidate) => Math.abs(candidate.y - y) <= 3);
      if (!row) {
        row = { y, items: [] };
        visualRows.push(row);
      }
      row.items.push({ x, text });
    }
    visualRows.sort((a, b) => b.y - a.y);
    for (let index = 0; index < visualRows.length; index += 1) {
      const row = visualRows[index];
      const rowText = row.items.sort((a, b) => a.x - b.x).map((item) => item.text).join(" ");
      const period = parsePeriod(rowText, forcedYear);
      if (!period || period.year !== Number(forcedYear)) continue;
      const dueYear = period.month === 12 ? period.year + 1 : period.year;
      let dates = parseDates(rowText, dueYear);

      for (let offset = 1; dates.length < 6 && offset <= 2 && visualRows[index + offset]; offset += 1) {
        const next = visualRows[index + offset];
        if (row.y - next.y > 20) break;
        const nextText = next.items.sort((a, b) => a.x - b.x).map((item) => item.text).join(" ");
        if (parsePeriod(nextText, forcedYear)) break;
        dates = parseDates(`${rowText} ${nextText}`, dueYear);
      }
      if (dates.length < 6) continue;
      schedule.set(`${period.year}-${period.month}`, Object.fromEntries(
        scheduleGroups.map((group, groupIndex) => [group, dates[groupIndex]]),
      ));
    }
  }
  await document.cleanup();
  await loadingTask.destroy();
  return schedule;
}

function rucGroup(ruc) {
  const digit = String(ruc || "").slice(-1);
  if (digit === "0" || digit === "1") return digit;
  if (digit === "2" || digit === "3") return "23";
  if (digit === "4" || digit === "5") return "45";
  if (digit === "6" || digit === "7") return "67";
  if (digit === "8" || digit === "9") return "89";
  return null;
}

function easterSunday(year) {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(Date.UTC(year, month - 1, day));
}

function peruHolidays(year) {
  const fixed = [
    [1, 1], [5, 1], [6, 7], [6, 29], [7, 23], [7, 28], [7, 29],
    [8, 6], [8, 30], [10, 8], [11, 1], [12, 8], [12, 9], [12, 25],
  ];
  const values = new Set(fixed.map(([month, day]) => `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`));
  const easter = easterSunday(year);
  for (const daysBefore of [3, 2]) {
    const holiday = new Date(easter);
    holiday.setUTCDate(holiday.getUTCDate() - daysBefore);
    values.add(dateISO(holiday));
  }
  return values;
}

function subtractBusinessDays(dateValue, daysBefore) {
  const date = new Date(`${dateValue}T00:00:00Z`);
  let remaining = Number(daysBefore);
  while (remaining > 0) {
    date.setUTCDate(date.getUTCDate() - 1);
    const weekday = date.getUTCDay();
    const holidays = peruHolidays(date.getUTCFullYear());
    if (weekday !== 0 && weekday !== 6 && !holidays.has(dateISO(date))) remaining -= 1;
  }
  return dateISO(date);
}

async function previewPdfSchedule(event) {
  const data = bodyOf(event);
  requireFields(data, ["kind", "file_base64", "year", "months", "days_before"]);
  if (!["pdt", "le"].includes(data.kind)) {
    throw Object.assign(new Error("El tipo de cronograma no es válido."), { status: 400 });
  }
  if (!Array.isArray(data.months) || !data.months.length) {
    throw Object.assign(new Error("Selecciona al menos un periodo."), { status: 400 });
  }
  const year = Number(data.year);
  const months = [...new Set(data.months.map(Number))];
  const daysBefore = Number(data.days_before);
  if (!Number.isInteger(year) || year < 2024 || year > 2100) {
    throw Object.assign(new Error("El año del cronograma no es válido."), { status: 400 });
  }
  if (months.some((month) => !Number.isInteger(month) || month < 1 || month > 12)) {
    throw Object.assign(new Error("Uno de los periodos seleccionados no es válido."), { status: 400 });
  }
  if (!Number.isInteger(daysBefore) || daysBefore < 1 || daysBefore > 10) {
    throw Object.assign(new Error("Los días hábiles deben estar entre 1 y 10."), { status: 400 });
  }
  const base64 = String(data.file_base64).replace(/^data:application\/pdf;base64,/, "");
  const buffer = Buffer.from(base64, "base64");
  if (!buffer.length || buffer.length > 4 * 1024 * 1024 || buffer.subarray(0, 4).toString() !== "%PDF") {
    throw Object.assign(new Error("El PDF no es válido o supera el límite de 4 MB."), { status: 400 });
  }
  const parsed = await extractScheduleFromPdf(buffer, year);
  if (!parsed.size) {
    throw Object.assign(new Error("No se reconoció la tabla del cronograma. Verifica que sea el PDF oficial de SUNAT y que contenga texto seleccionable."), { status: 422 });
  }

  const taskSql = data.kind === "pdt"
    ? `SELECT t.id,t.nombre_tarea,p.nombre_proyecto FROM tareas t
       JOIN proyectos p ON p.id=t.proyecto_id
       WHERE t.nombre_tarea ILIKE '%PDT%621%'
       ORDER BY p.nombre_proyecto,t.nombre_tarea`
    : `SELECT t.id,t.nombre_tarea,p.nombre_proyecto FROM tareas t
       JOIN proyectos p ON p.id=t.proyecto_id
       WHERE t.nombre_tarea ILIKE '%LE%V-C%VALIDACION%'
          OR (t.nombre_tarea ILIKE '%LE%V-C%' AND t.nombre_tarea NOT ILIKE '%VALIDACION%')
       ORDER BY CASE WHEN t.nombre_tarea ILIKE '%VALIDACION%' THEN 1 ELSE 2 END,t.nombre_tarea`;
  const [tasksResult, companiesResult, existingResult] = await Promise.all([
    pool.query(taskSql),
    pool.query("SELECT id,alias,razon_social,ruc FROM empresas WHERE estado_contrato='Activo' ORDER BY razon_social"),
    pool.query(
      "SELECT empresa_id,tarea_id,periodo_anio,periodo_mes FROM cronograma_pdt WHERE periodo_anio=$1 AND periodo_mes=ANY($2::int[])",
      [year, months],
    ),
  ]);
  if (!tasksResult.rows.length) {
    throw Object.assign(new Error(data.kind === "pdt"
      ? "No se encontró una tarea PDT 621 en el catálogo."
      : "No se encontraron las tareas LE V-C y LE V-C VALIDACION en el catálogo."), { status: 422 });
  }
  const existing = new Set(existingResult.rows.map((row) => `${row.empresa_id}-${row.tarea_id}-${row.periodo_anio}-${row.periodo_mes}`));
  const rows = [];
  for (const month of months.sort((a, b) => a - b)) {
    const dates = parsed.get(`${year}-${month}`);
    if (!dates) continue;
    for (const company of companiesResult.rows) {
      const sunatDate = dates[rucGroup(company.ruc)];
      if (!sunatDate) continue;
      for (const task of tasksResult.rows) {
        const key = `${company.id}-${task.id}-${year}-${month}`;
        rows.push({
          empresa_id: company.id,
          empresa: company.alias,
          razon_social: company.razon_social,
          ruc: company.ruc,
          tarea_id: task.id,
          tarea: task.nombre_tarea,
          periodo_mes: month,
          periodo_anio: year,
          fecha_sunat: sunatDate,
          fecha_vencimiento: subtractBusinessDays(sunatDate, daysBefore),
          exists: existing.has(key),
        });
      }
    }
  }
  return {
    rows,
    taskNames: tasksResult.rows.map((task) => task.nombre_tarea),
    parsedPeriods: [...parsed.keys()],
    newCount: rows.filter((row) => !row.exists).length,
    existingCount: rows.filter((row) => row.exists).length,
  };
}

async function listSchedule(event) {
  const query = event.queryStringParameters || {};
  const month = Number(query.month || new Date().getMonth() + 1);
  const year = Number(query.year || new Date().getFullYear());
  const { rows } = await pool.query(`
    WITH pdf_rows AS (
      SELECT cp.id::text id,cp.periodo_mes,cp.periodo_anio,cp.fecha_vencimiento,
        EXISTS (
          SELECT 1 FROM asignaciones a
          WHERE a.empresa_id=cp.empresa_id AND a.tarea_id=cp.tarea_id
            AND a.fecha_meta=cp.fecha_vencimiento
        ) asignado,
        e.id empresa_id,e.alias empresa,e.razon_social,e.ruc,
        t.id tarea_id,t.nombre_tarea tarea,p.nombre_proyecto proyecto,'pdf' origen
      FROM cronograma_pdt cp JOIN empresas e ON e.id=cp.empresa_id
      JOIN tareas t ON t.id=cp.tarea_id JOIN proyectos p ON p.id=t.proyecto_id
      WHERE cp.periodo_mes=$1 AND cp.periodo_anio=$2
    ), manual_rows AS (
      SELECT DISTINCT ON (a.id)
        'manual_'||a.id::text id,
        EXTRACT(MONTH FROM a.fecha_meta)::int periodo_mes,
        EXTRACT(YEAR FROM a.fecha_meta)::int periodo_anio,
        a.fecha_meta fecha_vencimiento,TRUE asignado,
        e.id empresa_id,e.alias empresa,e.razon_social,e.ruc,
        t.id tarea_id,t.nombre_tarea tarea,p.nombre_proyecto proyecto,'manual' origen
      FROM asignaciones a JOIN empresas e ON e.id=a.empresa_id
      JOIN tareas t ON t.id=a.tarea_id JOIN proyectos p ON p.id=t.proyecto_id
      WHERE EXTRACT(MONTH FROM a.fecha_meta)=$1 AND EXTRACT(YEAR FROM a.fecha_meta)=$2
        AND NOT EXISTS (
          SELECT 1 FROM cronograma_pdt cp
          WHERE cp.empresa_id=a.empresa_id AND cp.tarea_id=a.tarea_id
            AND cp.fecha_vencimiento=a.fecha_meta
        )
      ORDER BY a.id,a.usuario_id
    )
    SELECT * FROM pdf_rows
    UNION ALL
    SELECT * FROM manual_rows
    ORDER BY fecha_vencimiento,empresa`, [month, year]);
  return rows;
}

async function importSchedule(event) {
  const data = bodyOf(event);
  if (!Array.isArray(data.rows) || !data.rows.length) {
    throw Object.assign(new Error("No hay filas para importar."), { status: 400 });
  }
  const client = await pool.connect();
  let inserted = 0;
  try {
    await client.query("BEGIN");
    for (const row of data.rows) {
      requireFields(row, ["tarea_id", "empresa_id", "periodo_mes", "periodo_anio", "fecha_vencimiento"]);
      const result = await client.query(`
        INSERT INTO cronograma_pdt (tarea_id,empresa_id,periodo_mes,periodo_anio,fecha_vencimiento)
        SELECT $1,$2,$3,$4,$5
        WHERE NOT EXISTS (
          SELECT 1 FROM cronograma_pdt
          WHERE tarea_id=$1 AND empresa_id=$2 AND periodo_mes=$3 AND periodo_anio=$4
        )`, [row.tarea_id, row.empresa_id, row.periodo_mes, row.periodo_anio, row.fecha_vencimiento]);
      inserted += result.rowCount;
    }
    await client.query("COMMIT");
    return { inserted, skipped: data.rows.length - inserted };
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

async function assignSchedule(event, scheduleId) {
  const data = bodyOf(event);
  requireFields(data, ["usuario_ids"]);
  if (!data.usuario_ids.length) throw Object.assign(new Error("Selecciona al menos un trabajador."), { status: 400 });
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const item = await client.query("SELECT * FROM cronograma_pdt WHERE id=$1 FOR UPDATE", [scheduleId]);
    if (!item.rowCount) throw Object.assign(new Error("Registro de cronograma no encontrado."), { status: 404 });
    const next = await client.query("SELECT get_next_asignacion_id() nuevo_id");
    const id = next.rows[0].nuevo_id;
    for (const userId of [...new Set(data.usuario_ids)]) {
      await client.query(
        `INSERT INTO asignaciones (id,usuario_id,empresa_id,tarea_id,fecha_meta,estado,peso)
         OVERRIDING SYSTEM VALUE VALUES ($1,$2,$3,$4,$5,'pendiente',$6)`,
        [id, userId, item.rows[0].empresa_id, item.rows[0].tarea_id,
          item.rows[0].fecha_vencimiento, data.peso || 1],
      );
    }
    await client.query("UPDATE cronograma_pdt SET asignado=true WHERE id=$1", [scheduleId]);
    await client.query("COMMIT");
    return { assignmentId: id };
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

async function workerTasks(userId) {
  const { rows } = await pool.query(`
    SELECT a.id,t.nombre_tarea titulo,p.nombre_proyecto proyecto,a.fecha_meta fecha_limite,
      a.estado,e.razon_social empresa,e.alias empresa_alias,a.peso,
      rt.fecha_realizada,rt.rendimiento
    FROM asignaciones a JOIN tareas t ON t.id=a.tarea_id
    JOIN proyectos p ON p.id=t.proyecto_id JOIN empresas e ON e.id=a.empresa_id
    LEFT JOIN registros_tareas rt ON rt.asignacion_id=a.id AND rt.usuario_id=a.usuario_id
    WHERE a.usuario_id=$1 ORDER BY
      CASE WHEN a.estado='completada' THEN 1 ELSE 0 END,a.fecha_meta`, [userId]);
  return rows;
}

async function workerTaskDetail(id, user) {
  const params = [id];
  let condition = "";
  if (user.rol !== "admin") {
    params.push(user.id);
    condition = "AND a.usuario_id=$2";
  }
  const { rows } = await pool.query(`
    SELECT a.id,a.fecha_meta,a.estado,a.peso,e.razon_social empresa,e.alias empresa_alias,
      e.ruc,t.nombre_tarea tarea,p.nombre_proyecto proyecto,u.nom_res encargado,
      a.usuario_id,a.tarea_id,a.empresa_id,rt.fecha_realizada,rt.rendimiento
    FROM asignaciones a JOIN empresas e ON e.id=a.empresa_id
    JOIN tareas t ON t.id=a.tarea_id JOIN proyectos p ON p.id=t.proyecto_id
    JOIN usuarios u ON u.id=a.usuario_id
    LEFT JOIN registros_tareas rt ON rt.asignacion_id=a.id AND rt.usuario_id=a.usuario_id
    WHERE a.id=$1 ${condition} LIMIT 1`, params);
  if (!rows[0]) throw Object.assign(new Error("Tarea no encontrada."), { status: 404 });
  return rows[0];
}

function performance(doneDate, dueDate) {
  const done = new Date(`${String(doneDate).slice(0, 10)}T12:00:00`);
  const due = new Date(`${String(dueDate).slice(0, 10)}T12:00:00`);
  const days = Math.round((done - due) / 86_400_000);
  return days <= 0 ? "OPTIMO" : days <= 3 ? "MEDIO" : "BAJO";
}

async function updateWorkerTask(event, id, user) {
  const data = bodyOf(event);
  requireFields(data, ["estado", "fecha_realizada"]);
  requireAssignmentState(data.estado);
  const detail = await workerTaskDetail(id, user);
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const group = data.estado === "completada"
      ? await client.query(
          "SELECT id,usuario_id FROM asignaciones WHERE tarea_id=$1 AND empresa_id=$2 AND fecha_meta=$3",
          [detail.tarea_id, detail.empresa_id, detail.fecha_meta],
        )
      : { rows: [{ id: detail.id, usuario_id: detail.usuario_id }] };
    const rating = performance(data.fecha_realizada, detail.fecha_meta);
    for (const row of group.rows) {
      const existing = await client.query(
        "SELECT id FROM registros_tareas WHERE asignacion_id=$1 AND usuario_id=$2 LIMIT 1",
        [row.id, row.usuario_id],
      );
      if (existing.rowCount) {
        await client.query(
          "UPDATE registros_tareas SET fecha_realizada=$1,rendimiento=$2 WHERE id=$3",
          [data.fecha_realizada, rating, existing.rows[0].id],
        );
      } else {
        await client.query(
          "INSERT INTO registros_tareas (asignacion_id,usuario_id,fecha_realizada,rendimiento) VALUES ($1,$2,$3,$4)",
          [row.id, row.usuario_id, data.fecha_realizada, rating],
        );
      }
    }
    if (data.estado === "completada") {
      await client.query(
        "UPDATE asignaciones SET estado='completada' WHERE tarea_id=$1 AND empresa_id=$2 AND fecha_meta=$3",
        [detail.tarea_id, detail.empresa_id, detail.fecha_meta],
      );
    } else {
      await client.query("UPDATE asignaciones SET estado=$1 WHERE id=$2", [data.estado, id]);
    }
    await client.query("COMMIT");
    return { rendimiento: rating };
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

async function getProfile(userId) {
  const [profile, stats] = await Promise.all([
    pool.query(`
      SELECT u.id,u.nom_res,u.alias,u.usuario,u.rol,u.estado,u.fecha_creacion,
        a.nombre_area,s.nombre_subarea
      FROM usuarios u LEFT JOIN subareas s ON s.id=u.subarea_id
      LEFT JOIN areas a ON a.id=s.area_id WHERE u.id=$1`, [userId]),
    pool.query(`
      SELECT COUNT(*)::int total,
        COUNT(*) FILTER (WHERE a.estado='completada')::int completadas,
        COUNT(*) FILTER (WHERE a.estado='pendiente')::int pendientes,
        COUNT(*) FILTER (WHERE rt.rendimiento='OPTIMO')::int optimas
      FROM asignaciones a LEFT JOIN registros_tareas rt
        ON rt.asignacion_id=a.id AND rt.usuario_id=a.usuario_id
      WHERE a.usuario_id=$1`, [userId]),
  ]);
  return { profile: profile.rows[0], stats: stats.rows[0] };
}

async function removeRecord(table, id) {
  const allowed = new Set(["usuarios", "empresas", "tareas"]);
  if (!allowed.has(table)) throw Object.assign(new Error("Recurso inválido."), { status: 400 });
  const result = await pool.query(`DELETE FROM ${table} WHERE id=$1`, [id]);
  if (!result.rowCount) throw Object.assign(new Error("Registro no encontrado."), { status: 404 });
}

export async function handler(event) {
  const method = event.httpMethod;
  const path = normalizePath(event);
  try {
    if (method === "OPTIONS") return { statusCode: 204, headers };
    if (path === "/health" && method === "GET") {
      await pool.query("SELECT 1");
      return json(200, { ok: true, database: "connected" });
    }
    if (path === "/auth/login" && method === "POST") return login(event);
    if (path === "/auth/logout" && method === "POST") {
      return json(200, { ok: true }, { "Set-Cookie": clearSessionCookie(event) });
    }
    if (path === "/auth/me" && method === "GET") {
      const user = ensureAuth(event);
      return json(200, { user });
    }

    const user = ensureAuth(event);
    if (path === "/profile" && method === "GET") return json(200, await getProfile(user.id));
    if (path === "/worker/tasks" && method === "GET") return json(200, await workerTasks(user.id));
    const workerTaskMatch = path.match(/^\/worker\/tasks\/(\d+)$/);
    if (workerTaskMatch && method === "GET") return json(200, await workerTaskDetail(Number(workerTaskMatch[1]), user));
    if (workerTaskMatch && method === "PUT") return json(200, await updateWorkerTask(event, Number(workerTaskMatch[1]), user));

    ensureAuth(event, "admin");
    if (path === "/dashboard" && method === "GET") return json(200, await getDashboard());
    if (path === "/references" && method === "GET") return json(200, await getReferences());

    if (path === "/users" && method === "GET") return json(200, await listUsers());
    if (path === "/users" && method === "POST") return json(201, await createUser(event));
    const userMatch = path.match(/^\/users\/(\d+)$/);
    if (userMatch && method === "PUT") {
      await updateUser(event, Number(userMatch[1]));
      return json(200, { ok: true });
    }
    if (userMatch && method === "DELETE") {
      await removeRecord("usuarios", Number(userMatch[1]));
      return json(200, { ok: true });
    }

    if (path === "/companies" && method === "GET") return json(200, await listCompanies());
    if (path === "/companies" && method === "POST") return json(201, await createCompany(event));
    const companyMatch = path.match(/^\/companies\/(\d+)$/);
    if (companyMatch && method === "GET") return json(200, await companyDetail(Number(companyMatch[1])));
    if (companyMatch && method === "PUT") {
      await updateCompany(event, Number(companyMatch[1]));
      return json(200, { ok: true });
    }
    if (companyMatch && method === "DELETE") {
      await removeRecord("empresas", Number(companyMatch[1]));
      return json(200, { ok: true });
    }

    if (path === "/tasks" && method === "GET") return json(200, await listTasks());
    if (path === "/tasks" && method === "POST") return json(201, await createTask(event));
    const taskMatch = path.match(/^\/tasks\/(\d+)$/);
    if (taskMatch && method === "PUT") {
      await updateTask(event, Number(taskMatch[1]));
      return json(200, { ok: true });
    }
    if (taskMatch && method === "DELETE") {
      await removeRecord("tareas", Number(taskMatch[1]));
      return json(200, { ok: true });
    }

    if (path === "/assignments" && method === "GET") return json(200, await listAssignments(event));
    if (path === "/assignments" && method === "POST") return json(201, await createAssignment(event));
    const assignmentMatch = path.match(/^\/assignments\/(\d+)$/);
    if (assignmentMatch && method === "PUT") {
      await updateAssignment(event, Number(assignmentMatch[1]));
      return json(200, { ok: true });
    }
    if (assignmentMatch && method === "DELETE") {
      await deleteAssignment(Number(assignmentMatch[1]));
      return json(200, { ok: true });
    }

    if (path === "/schedule" && method === "GET") return json(200, await listSchedule(event));
    if (path === "/schedule/preview-pdf" && method === "POST") return json(200, await previewPdfSchedule(event));
    if (path === "/schedule/import" && method === "POST") return json(200, await importSchedule(event));
    const scheduleAssignMatch = path.match(/^\/schedule\/(\d+)\/assign$/);
    if (scheduleAssignMatch && method === "POST") {
      return json(201, await assignSchedule(event, Number(scheduleAssignMatch[1])));
    }
    return json(404, { error: "Ruta no encontrada." });
  } catch (error) {
    const code = error.code === "23505" ? 409
      : error.code === "23503" ? 409
      : error.status || 500;
    if (code >= 500) console.error(error);
    const message = error.code === "23505"
      ? "Ya existe un registro con esos datos."
      : error.code === "23503"
        ? "No se puede eliminar porque el registro está siendo utilizado."
        : error.message || "Ocurrió un error inesperado.";
    return json(code, { error: message });
  }
}
