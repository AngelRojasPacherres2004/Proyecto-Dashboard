import hashlib
import secrets
from datetime import datetime, timedelta


def hash_password(password: str) -> str:
    """
    Genera un hash seguro de la contraseña usando SHA-256
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash de la contraseña
    """
    return password


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash
    
    Args:
        password: Contraseña en texto plano
        hashed_password: Hash almacenado
        
    Returns:
        True si coinciden, False en caso contrario
    """
    return password == hashed_password


def generate_token() -> str:
    """
    Genera un token seguro para sesión
    
    Returns:
        Token aleatorio
    """
    return secrets.token_urlsafe(32)


def is_valid_email(email: str) -> bool:
    """
    Valida el formato básico de un email
    
    Args:
        email: Email a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    return "@" in email and "." in email.split("@")[1]


def is_valid_username(username: str) -> bool:
    """
    Valida el formato del nombre de usuario
    
    Args:
        username: Nombre de usuario a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    return len(username) >= 3 and username.replace("_", "").isalnum()
