from config.BD_Client import get_connection
from utils.auth import hash_password, verify_password, is_valid_email, is_valid_username


def crear_usuario(nombre: str, email: str, username: str, password: str, rol: str = "trabajador") -> dict:
    """
    Crea un nuevo usuario en la base de datos
    
    Args:
        nombre: Nombre completo del usuario
        email: Email del usuario
        username: Nombre de usuario único
        password: Contraseña en texto plano
        rol: Rol del usuario (admin, trabajador)
        
    Returns:
        Dict con resultado de la operación
    """
    # Validaciones
    if not nombre or len(nombre) < 2:
        return {"exito": False, "mensaje": "El nombre debe tener al menos 2 caracteres"}
    
    if not is_valid_email(email):
        return {"exito": False, "mensaje": "Email inválido"}
    
    if not is_valid_username(username):
        return {"exito": False, "mensaje": "El nombre de usuario debe tener al menos 3 caracteres y solo contener letras, números y guiones bajos"}
    
    if not password or len(password) < 4:
        return {"exito": False, "mensaje": "La contraseña debe tener al menos 4 caracteres"}
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Hashear la contraseña
        password_hash = hash_password(password)
        
        # Insertar el usuario
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, username, password, rol)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, email, username, password_hash, rol))
        
        conn.commit()
        usuario_id = cursor.lastrowid
        conn.close()
        
        return {"exito": True, "mensaje": "Usuario creado exitosamente", "usuario_id": usuario_id}
    
    except sqlite3.IntegrityError as e:
        if "email" in str(e):
            return {"exito": False, "mensaje": "El email ya está registrado"}
        elif "username" in str(e):
            return {"exito": False, "mensaje": "El nombre de usuario ya está en uso"}
        return {"exito": False, "mensaje": "Error al crear el usuario"}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error: {str(e)}"}


def obtener_usuario_por_username(username: str) -> dict:
    """
    Obtiene un usuario por su nombre de usuario
    
    Args:
        username: Nombre de usuario a buscar
        
    Returns:
        Diccionario con los datos del usuario o None si no existe
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                "id": resultado["id"],
                "nombre": resultado["nombre"],
                "email": resultado["email"],
                "username": resultado["username"],
                "password": resultado["password"],
                "rol": resultado["rol"],
                "estado": resultado["estado"],
                "fecha_creacion": resultado["fecha_creacion"]
            }
        return None
    except Exception as e:
        print(f"Error al obtener usuario: {str(e)}")
        return None


def obtener_usuario_por_email(email: str) -> dict:
    """
    Obtiene un usuario por su email
    
    Args:
        email: Email a buscar
        
    Returns:
        Diccionario con los datos del usuario o None si no existe
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                "id": resultado["id"],
                "nombre": resultado["nombre"],
                "email": resultado["email"],
                "username": resultado["username"],
                "password": resultado["password"],
                "rol": resultado["rol"],
                "estado": resultado["estado"],
                "fecha_creacion": resultado["fecha_creacion"]
            }
        return None
    except Exception as e:
        print(f"Error al obtener usuario: {str(e)}")
        return None


def autenticar_usuario(username: str, password: str) -> dict:
    """
    Autentica un usuario con su nombre de usuario y contraseña
    
    Args:
        username: Nombre de usuario
        password: Contraseña en texto plano
        
    Returns:
        Dict con resultado de la autenticación
    """
    usuario = obtener_usuario_por_username(username)
    
    if not usuario:
        return {"exito": False, "mensaje": "Usuario no encontrado"}
    
    if usuario["estado"] != "activo":
        return {"exito": False, "mensaje": "El usuario está inactivo"}
    
    if verify_password(password, usuario["password"]):
        return {
            "exito": True,
            "mensaje": "Autenticación exitosa",
            "usuario": {
                "id": usuario["id"],
                "nombre": usuario["nombre"],
                "email": usuario["email"],
                "username": usuario["username"],
                "rol": usuario["rol"]
            }
        }
    else:
        return {"exito": False, "mensaje": "Contraseña incorrecta"}


def obtener_todos_usuarios() -> list:
    """
    Obtiene todos los usuarios de la base de datos
    
    Returns:
        Lista de usuarios
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nombre, email, username, rol, estado, fecha_creacion 
            FROM usuarios ORDER BY fecha_creacion DESC
        """)
        
        usuarios = []
        for row in cursor.fetchall():
            usuarios.append({
                "id": row["id"],
                "nombre": row["nombre"],
                "email": row["email"],
                "username": row["username"],
                "rol": row["rol"],
                "estado": row["estado"],
                "fecha_creacion": row["fecha_creacion"]
            })
        
        conn.close()
        return usuarios
    except Exception as e:
        print(f"Error al obtener usuarios: {str(e)}")
        return []


def actualizar_usuario(usuario_id: int, **kwargs) -> dict:
    """
    Actualiza los datos de un usuario
    
    Args:
        usuario_id: ID del usuario a actualizar
        **kwargs: Campos a actualizar (nombre, email, rol, estado, etc.)
        
    Returns:
        Dict con resultado de la operación
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Construir la consulta dinámicamente
        campos = []
        valores = []
        
        for campo, valor in kwargs.items():
            if campo in ["nombre", "email", "username", "rol", "estado"]:
                campos.append(f"{campo} = ?")
                valores.append(valor)
        
        if not campos:
            return {"exito": False, "mensaje": "No hay campos para actualizar"}
        
        valores.append(usuario_id)
        
        query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"
        cursor.execute(query, valores)
        
        conn.commit()
        conn.close()
        
        return {"exito": True, "mensaje": "Usuario actualizado correctamente"}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al actualizar: {str(e)}"}


def eliminar_usuario(usuario_id: int) -> dict:
    """
    Elimina un usuario de la base de datos
    
    Args:
        usuario_id: ID del usuario a eliminar
        
    Returns:
        Dict con resultado de la operación
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conn.commit()
        conn.close()
        
        return {"exito": True, "mensaje": "Usuario eliminado correctamente"}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al eliminar: {str(e)}"}


# Importar sqlite3 al final para evitar problemas de importación circular
import sqlite3
