BEGIN;

-- AES-256-GCM produce valores mayores que los varchar(50) originales.
ALTER TABLE empresas
  ALTER COLUMN sunat_usuario TYPE TEXT USING sunat_usuario::text,
  ALTER COLUMN sunat_clave TYPE TEXT USING sunat_clave::text,
  ALTER COLUMN afpnet_usuario TYPE TEXT USING afpnet_usuario::text,
  ALTER COLUMN afpnet_clave TYPE TEXT USING afpnet_clave::text,
  ALTER COLUMN bn_usuario TYPE TEXT USING bn_usuario::text,
  ALTER COLUMN bn_clave TYPE TEXT USING bn_clave::text;

-- Unicidad lógica sin depender de mayúsculas y minúsculas.
CREATE UNIQUE INDEX IF NOT EXISTS usuarios_usuario_lower_ux
  ON usuarios (LOWER(usuario));

CREATE UNIQUE INDEX IF NOT EXISTS tareas_proyecto_nombre_lower_ux
  ON tareas (proyecto_id, LOWER(nombre_tarea));

CREATE UNIQUE INDEX IF NOT EXISTS registros_tareas_asignacion_usuario_ux
  ON registros_tareas (asignacion_id, usuario_id);

-- Restricciones e índices para las reglas operativas.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname='asignaciones_peso_check'
      AND conrelid='asignaciones'::regclass
  ) THEN
    ALTER TABLE asignaciones
      ADD CONSTRAINT asignaciones_peso_check CHECK (peso BETWEEN 1 AND 10);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS asignaciones_estado_fecha_idx
  ON asignaciones (estado, fecha_meta);

CREATE INDEX IF NOT EXISTS asignaciones_empresa_tarea_fecha_idx
  ON asignaciones (empresa_id, tarea_id, fecha_meta);

CREATE INDEX IF NOT EXISTS cronograma_periodo_idx
  ON cronograma_pdt (periodo_anio, periodo_mes, fecha_vencimiento);

-- Corrige estados existentes al aplicar la migración.
UPDATE asignaciones
SET estado='vencida'
WHERE estado='pendiente' AND fecha_meta<CURRENT_DATE;

UPDATE cronograma_pdt cp
SET asignado=EXISTS(
  SELECT 1 FROM asignaciones a
  WHERE a.empresa_id=cp.empresa_id
    AND a.tarea_id=cp.tarea_id
    AND a.fecha_meta=cp.fecha_vencimiento
)
WHERE cp.asignado IS DISTINCT FROM EXISTS(
  SELECT 1 FROM asignaciones a
  WHERE a.empresa_id=cp.empresa_id
    AND a.tarea_id=cp.tarea_id
    AND a.fecha_meta=cp.fecha_vencimiento
);

COMMIT;
