# Nexo Contable

Migración del dashboard original de Streamlit a React, con una API serverless para Netlify y PostgreSQL.

## Arquitectura

- `src/`: interfaz React y sistema visual responsive.
- `netlify/functions/api.js`: API privada, autenticación, permisos y acceso a PostgreSQL.
- `scripts/dev-api.js`: servidor de API únicamente para desarrollo local.
- `netlify.toml`: build, funciones y redirecciones para Netlify.
- Los archivos Python originales se conservan como referencia y respaldo; ya no son necesarios para el despliegue React.

La URL de PostgreSQL nunca se envía al navegador. Todas las consultas pasan por la función serverless y las rutas administrativas validan el rol del usuario.

## Desarrollo local

Requiere Node.js 22 o superior.

```bash
npm install
npm run dev
```

La aplicación queda disponible en `http://127.0.0.1:5180`. El comando inicia tanto React como la API local.

Variables requeridas en `.env`:

```env
DATABASE_URL=postgresql://...
JWT_SECRET=un-secreto-largo
CREDENTIALS_ENCRYPTION_KEY=clave-hexadecimal-de-64-caracteres
```

Para generar valores seguros:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Ejecuta el comando dos veces: una para `JWT_SECRET` y otra para `CREDENTIALS_ENCRYPTION_KEY`.

## Despliegue en Netlify

1. Sube el proyecto a GitHub y crea un sitio desde ese repositorio.
2. Netlify detectará `netlify.toml`:
   - Build command: `npm run build`
   - Publish directory: `dist`
   - Functions directory: `netlify/functions`
3. En **Site configuration → Environment variables**, agrega:
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `CREDENTIALS_ENCRYPTION_KEY`
4. Despliega el sitio.
5. Comprueba `https://tu-sitio.netlify.app/api/health`; debe responder que la base está conectada.

No configures secretos con el prefijo `VITE_`: ese prefijo los haría visibles en el frontend.

## Seguridad incorporada

- Sesión firmada en cookie `HttpOnly`, `Secure` y `SameSite=Lax`.
- Rutas protegidas por rol (`admin` y `trabajador`).
- Contraseñas nuevas con bcrypt.
- Las contraseñas antiguas en texto plano se convierten automáticamente a bcrypt después de un inicio de sesión correcto.
- Límite básico de intentos de acceso.
- Cifrado AES-256-GCM para nuevas credenciales SUNAT, AFPnet y Banco de la Nación en producción.
- Consultas parametrizadas contra PostgreSQL.

## Verificación

```bash
npm run check
npm run build
npm run qa:integration
```

La compilación de producción se genera en `dist/`.

`qa:integration` crea datos temporales con prefijo QA, prueba autenticación,
permisos, CRUD, vencimientos, progreso, rendimiento y cronograma, y elimina
esos datos al finalizar aunque una prueba falle.

## Migraciones de base de datos

Para una base existente que todavía conserve las columnas originales:

```bash
npm run db:migrate
```

La migración amplía las columnas de credenciales para soportar AES-256-GCM,
añade restricciones de integridad e índices, y sincroniza vencimientos e
indicadores del cronograma. Es idempotente y puede ejecutarse nuevamente.
