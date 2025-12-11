"""
Endpoints de Autenticación - Registro, Login, Google Auth, Refresh Token.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import secrets
import string

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
from app.core.security import create_access_token, create_refresh_token, get_password_hash

router = APIRouter()


class GoogleTokenRequest(BaseModel):
    token: str


def generate_random_password(length: int = 32) -> str:
    """Genera una contraseña aleatoria para usuarios de Google"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


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
    "/google",
    response_model=dict,
    summary="Autenticación con Google",
    description="Autentica o registra un usuario usando Google OAuth."
)
async def google_auth(
    request: GoogleTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Autenticar usuario con token de Google.
    Si el usuario no existe, lo crea automáticamente.
    """
    try:
        # Verificar token con Google
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/userinfo/v2/me',
                headers={'Authorization': f'Bearer {request.token}'}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token de Google inválido"
                )
            
            google_user = response.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error conectando con Google"
        )

    email = google_user.get('email')
    name = google_user.get('name', '')
    picture = google_user.get('picture', '')

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener el email de Google"
        )

    # Buscar usuario existente
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Crear nuevo usuario
        random_password = generate_random_password()
        user = User(
            email=email,
            full_name=name,
            hashed_password=get_password_hash(random_password),
            avatar_url=picture,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generar tokens JWT
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return {
        "message": "Autenticación exitosa con Google",
        "user": UserResponse.model_validate(user),
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    }


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
    """
    return UserResponse.model_validate(current_user)
