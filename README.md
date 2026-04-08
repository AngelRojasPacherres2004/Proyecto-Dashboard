# 📊 Dashboard de Gestión de Proyectos

Sistema de gestión de tareas y proyectos desarrollado con **Streamlit** y **SQLite**.

## 🎯 Características

- **🔐 Sistema de Autenticación**: Login y registro seguro de usuarios
- **👤 Gestión de Usuarios**: Diferenciación entre roles (admin, trabajador)
- **📝 Gestión de Tareas**: Crear, editar y completar tareas
- **📈 Seguimiento de Rendimiento**: Métricas y estadísticas de productividad
- **👥 Panel de Administración**: Gestión de usuarios y configuración del sistema

## 📋 Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## 🚀 Instalación

1. **Clona o descarga el proyecto**:
   ```bash
   cd Proyecto-Dashboard
   ```

2. **Crea un entorno virtual** (opcional pero recomendado):
   ```bash
   python -m venv venv
   ```

3. **Activa el entorno virtual**:
   
   - En Windows:
     ```bash
     venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Instala las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Inicializa la base de datos** (opcional, se hace automáticamente):
   ```bash
   python config/BD_Client.py
   ```

## ▶️ Ejecución

Para iniciar la aplicación:

```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

## 🔐 Primeras Credenciales

Cuando inicies el proyecto por primera vez:

1. Ve a la pestaña **"Registrarse"**
2. Crea una nueva cuenta
3. Usa esas credenciales para iniciar sesión

## 📁 Estructura del Proyecto

```
Proyecto-Dashboard/
├── app.py                          # Aplicación principal
├── requirements.txt                # Dependencias
├── config/
│   └── BD_Client.py               # Configuración de base de datos
├── pages/
│   └── login.py                   # Página de login
├── services/
│   ├── usuarios_services.py       # Servicios de usuarios
│   ├── tareas_services.py         # Servicios de tareas
│   └── rendimiento.py             # Cálculo de rendimiento
├── utils/
│   └── auth.py                    # Funciones de autenticación
└── data/
    └── proyecto.db                # Base de datos SQLite
```

## 🔒 Seguridad

- Las contraseñas se almacenan **hasheadas con SHA-256**
- Sesiones de usuario gestionadas por Streamlit
- Validación de entrada en formularios
- Base de datos SQLite con integridad referencial

## 🎨 Interfaz

- Diseño responsive con Streamlit
- Sidebar con menú de navegación
- Pestañas para organización de contenido
- Indicadores visuales (emojis) para mejor UX

## 📝 Próximos Pasos

- Implementar CRUD completo de tareas
- Agregar gráficos de rendimiento
- Integrar notificaciones
- Añadir filtros y búsqueda avanzada
- Exportar reportes

## 📄 Licencia

Proyecto personal - Todos los derechos reservados

## 💬 Soporte

Para reportar problemas o sugerencias, abre un issue.

---

**Desarrollado con ❤️ usando Streamlit**
