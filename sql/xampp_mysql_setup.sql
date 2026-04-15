CREATE DATABASE IF NOT EXISTS dashboard_proyectos
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'dashboard_user'@'localhost'
  IDENTIFIED BY 'dashboard123';

GRANT ALL PRIVILEGES ON dashboard_proyectos.* TO 'dashboard_user'@'localhost';
FLUSH PRIVILEGES;

USE dashboard_proyectos;

CREATE TABLE IF NOT EXISTS responsables (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom_res VARCHAR(120) NOT NULL,
  correo VARCHAR(150) NOT NULL UNIQUE,
  password_hash CHAR(64) NOT NULL,
  rol ENUM('admin', 'trabajador') NOT NULL DEFAULT 'trabajador',
  estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
  fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS registros_trabajador (
  id INT AUTO_INCREMENT PRIMARY KEY,
  anio INT NOT NULL,
  empresa VARCHAR(150) NOT NULL,
  proyecto VARCHAR(150) NOT NULL,
  tarea VARCHAR(200) NOT NULL,
  mes_t VARCHAR(40) NOT NULL,
  encargado VARCHAR(120) NOT NULL,
  fecha_realizada DATE NOT NULL,
  fecha_meta DATE NOT NULL,
  cantidad INT NOT NULL DEFAULT 0,
  prioridad ENUM('Alta', 'Media', 'Baja') NOT NULL,
  responsable_id INT NULL,
  fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_registro_responsable
    FOREIGN KEY (responsable_id) REFERENCES responsables(id)
    ON DELETE SET NULL
);

INSERT INTO responsables (nom_res, correo, password_hash, rol, estado)
SELECT 'Administrador', 'admin@dashboard.com', 'ac9689e2272427085e35b9d3e3e8bed88cb3434828b43b86fc0596cad4c6e270', 'admin', 'activo'
WHERE NOT EXISTS (
  SELECT 1 FROM responsables WHERE correo = 'admin@dashboard.com'
);

INSERT INTO responsables (nom_res, correo, password_hash, rol, estado)
SELECT 'Trabajador Demo', 'trabajador@dashboard.com', '2e80a850b7752ec924b107f72526449f7bbe5c6024777a1390b26525b01b5d05', 'trabajador', 'activo'
WHERE NOT EXISTS (
  SELECT 1 FROM responsables WHERE correo = 'trabajador@dashboard.com'
);
