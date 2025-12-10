"""
Módulo de seguridad - Manejo de contraseñas y tokens JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from jose import JWTError, jwt

from app.core.config import settings

# Límite de bcrypt para contraseñas
BCRYPT_MAX_LENGTH = 72

# Importar bcrypt de forma segura
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


def _truncate_password(password: str) -> bytes:
    """
    Trunca la contraseña a 72 bytes (límite de bcrypt) y la convierte a bytes.
    """
    password_bytes = password.encode('utf-8')
    return password_bytes[:BCRYPT_MAX_LENGTH]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con el hash.
    """
    if not BCRYPT_AVAILABLE:
        return False
    
    try:
        password_bytes = _truncate_password(plain_password)
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Error verificando password: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Genera hash seguro de una contraseña usando bcrypt.
    """
    if not BCRYPT_AVAILABLE:
        raise ValueError("bcrypt no disponible")
    
    try:
        password_bytes = _truncate_password(password)
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"Error hasheando password: {e}")
        raise ValueError(f"Error al procesar contraseña: {e}")


def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un JWT access token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un JWT refresh token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un token JWT.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None