import fs from "node:fs/promises";
import pg from "pg";

const database = new pg.Client({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

await database.connect();
try {
  const sql = await fs.readFile(new URL("../migrations/001_integrity_and_encryption.sql", import.meta.url), "utf8");
  await database.query(sql);
  console.log("Migración 001 aplicada correctamente.");
} finally {
  await database.end();
}
