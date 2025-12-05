"""
Schemas de Usuario - Validación de datos con Pydantic.
Define la estructura de requests y responses para usuarios.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================
# REQUEST SCHEMAS (Lo que recibe la API)
# ============================================

class UserCreate(BaseModel):
    """Schema para registro de nuevo usuario."""
    
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        description="Contraseña (mínimo 8 caracteres)"
    )
    full_name: str = Field(
        ..., 
        min_length=2, 
        max_length=255,
        description="Nombre completo del usuario"
    )
    birth_date: Optional[datetime] = Field(
        None, 
        description="Fecha de nacimiento"
    )


class UserLogin(BaseModel):
    """Schema para login de usuario."""
    
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña")


class UserUpdate(BaseModel):
    """Schema para actualizar datos del usuario."""
    
    full_name: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=255,
        description="Nombre completo"
    )
    birth_date: Optional[datetime] = Field(None, description="Fecha de nacimiento")
    weight_kg: Optional[float] = Field(
        None, 
        gt=0, 
        lt=500,
        description="Peso en kilogramos"
    )
    height_cm: Optional[float] = Field(
        None, 
        gt=0, 
        lt=300,
        description="Altura en centímetros"
    )
    avatar_url: Optional[str] = Field(
        None, 
        max_length=500,
        description="URL del avatar"
    )


# ============================================
# RESPONSE SCHEMAS (Lo que devuelve la API)
# ============================================

class UserResponse(BaseModel):
    """Schema de respuesta con datos del usuario."""
    
    id: int
    email: str
    full_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    total_points: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    level: int = 1
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# AUTH SCHEMAS (Tokens JWT)
# ============================================

class Token(BaseModel):
    """Schema de respuesta con tokens JWT."""
    
    access_token: str = Field(..., description="Token de acceso")
    refresh_token: str = Field(..., description="Token de refresco")
    token_type: str = Field(default="bearer", description="Tipo de token")


class TokenPayload(BaseModel):
    """Schema del payload decodificado del JWT."""
    
    sub: str = Field(..., description="ID del usuario")
    exp: int = Field(..., description="Timestamp de expiración")
    type: str = Field(..., description="Tipo de token (access/refresh)")


class RefreshTokenRequest(BaseModel):
    """Schema para solicitar nuevo access token."""
    
    refresh_token: str = Field(..., description="Token de refresco")