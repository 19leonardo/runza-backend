"""
Endpoint para autenticación con Google.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx

from app.db.base import get_db
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.schemas.user import UserResponse
import secrets
import string

router = APIRouter()


class GoogleTokenRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    message: str
    user: UserResponse
    tokens: dict


def generate_random_password(length: int = 32) -> str:
    """Genera una contraseña aleatoria para usuarios de Google"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleTokenRequest, db: Session = Depends(get_db)):
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
            is_verified=True,  # Google ya verificó el email
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generar tokens JWT
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return AuthResponse(
        message="Autenticación exitosa con Google",
        user=UserResponse.model_validate(user),
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    )