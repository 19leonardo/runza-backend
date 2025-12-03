"""
Dependencias de la API - Inyección de dependencias para FastAPI.
"""

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User
from app.services.auth_service import AuthService

# Esquema de seguridad Bearer Token
security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Dependency que provee el servicio de autenticación.
    
    Args:
        db: Sesión de base de datos (inyectada)
        
    Returns:
        Instancia de AuthService
    """
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency que obtiene el usuario actual del token JWT.
    Usar en endpoints que requieren autenticación.
    
    Args:
        credentials: Credenciales del header Authorization
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException 401: Si el token es inválido o expiró
    """
    auth_service = AuthService(db)
    user = auth_service.get_current_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency que verifica que el usuario esté activo.
    
    Args:
        current_user: Usuario del token (inyectado)
        
    Returns:
        Usuario activo
        
    Raises:
        HTTPException 403: Si el usuario está desactivado
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    return current_user