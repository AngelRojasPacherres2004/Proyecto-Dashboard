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

INSERT INTO responsables (nom_res, correo, password_hash, rol, estado)
SELECT 'Administrador', 'admin@dashboard.com', '123', 'admin', 'activo'
WHERE NOT EXISTS (
  SELECT 1 FROM responsables WHERE correo = 'admin@dashboard.com'
);

INSERT INTO responsables (nom_res, correo, password_hash, rol, estado)
SELECT 'Trabajador Demo', 'trabajador@dashboard.com', '123', 'trabajador', 'activo'
WHERE NOT EXISTS (
  SELECT 1 FROM responsables WHERE correo = 'trabajador@dashboard.com'
);
