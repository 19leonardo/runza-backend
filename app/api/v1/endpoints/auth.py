"""
Endpoints de Autenticación - Registro, Login, Refresh Token.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_auth_service, get_current_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    RefreshTokenRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea una nueva cuenta de usuario en el sistema RunZa."
)
def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Registra un nuevo usuario en el sistema.
    
    - **email**: Email único del usuario
    - **password**: Contraseña (mínimo 8 caracteres)
    - **full_name**: Nombre completo
    - **birth_date**: Fecha de nacimiento (opcional)
    """
    try:
        user, tokens = auth_service.register(user_data)
        
        return {
            "message": "Usuario registrado exitosamente",
            "user": UserResponse.model_validate(user),
            "tokens": tokens
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=dict,
    summary="Iniciar sesión",
    description="Autentica un usuario y devuelve tokens JWT."
)
def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Inicia sesión con email y contraseña.
    
    Devuelve access_token (30 min) y refresh_token (7 días).
    """
    try:
        user, tokens = auth_service.login(
            email=credentials.email,
            password=credentials.password
        )
        
        return {
            "message": "Login exitoso",
            "user": UserResponse.model_validate(user),
            "tokens": tokens
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renovar access token",
    description="Genera un nuevo access token usando el refresh token."
)
def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Renueva el access token usando un refresh token válido.
    """
    try:
        tokens = auth_service.refresh_access_token(request.refresh_token)
        return tokens
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener usuario actual",
    description="Devuelve los datos del usuario autenticado."
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los datos del usuario actual.
    
    Requiere autenticación con Bearer Token.
    """
    return UserResponse.model_validate(current_user)