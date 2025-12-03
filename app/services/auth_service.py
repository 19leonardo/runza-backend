"""
Servicio de Autenticación - Lógica de negocio para auth.
Maneja registro, login, y validación de tokens.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, Token


class AuthService:
    """
    Servicio que encapsula la lógica de autenticación.
    Separa la lógica de negocio de los endpoints.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa el servicio con una sesión de base de datos.
        
        Args:
            db: Sesión de SQLAlchemy
        """
        self.db = db
        self.user_repo = UserRepository(db)
    
    def register(self, user_data: UserCreate) -> Tuple[User, Token]:
        """
        Registra un nuevo usuario en el sistema.
        
        Args:
            user_data: Datos del usuario a registrar
            
        Returns:
            Tupla con (Usuario creado, Tokens JWT)
            
        Raises:
            ValueError: Si el email ya está registrado
        """
        # Verificar si el email ya existe
        if self.user_repo.exists_by_email(user_data.email):
            raise ValueError("El email ya está registrado")
        
        # Crear usuario con contraseña hasheada
        user_dict = {
            "email": user_data.email.lower(),
            "hashed_password": get_password_hash(user_data.password),
            "full_name": user_data.full_name,
            "birth_date": user_data.birth_date,
        }
        
        user = self.user_repo.create(user_dict)
        
        # Generar tokens
        tokens = self._generate_tokens(user.id)
        
        return user, tokens
    
    def login(self, email: str, password: str) -> Tuple[User, Token]:
        """
        Autentica un usuario con email y contraseña.
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Tupla con (Usuario autenticado, Tokens JWT)
            
        Raises:
            ValueError: Si las credenciales son inválidas
        """
        # Buscar usuario por email
        user = self.user_repo.get_by_email(email)
        
        if not user:
            raise ValueError("Credenciales inválidas")
        
        # Verificar contraseña
        if not verify_password(password, user.hashed_password):
            raise ValueError("Credenciales inválidas")
        
        # Verificar que la cuenta esté activa
        if not user.is_active:
            raise ValueError("La cuenta está desactivada")
        
        # Actualizar último login
        self.user_repo.update_last_login(user)
        
        # Generar tokens
        tokens = self._generate_tokens(user.id)
        
        return user, tokens
    
    def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Genera un nuevo access token usando el refresh token.
        
        Args:
            refresh_token: Token de refresco válido
            
        Returns:
            Nuevos tokens JWT
            
        Raises:
            ValueError: Si el refresh token es inválido
        """
        # Decodificar el refresh token
        payload = decode_token(refresh_token)
        
        if not payload:
            raise ValueError("Token de refresco inválido")
        
        # Verificar que sea un refresh token
        if payload.get("type") != "refresh":
            raise ValueError("Token de refresco inválido")
        
        # Obtener el usuario
        user_id = int(payload.get("sub"))
        user = self.user_repo.get_by_id(user_id)
        
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o inactivo")
        
        # Generar nuevos tokens
        return self._generate_tokens(user.id)
    
    def get_current_user(self, token: str) -> Optional[User]:
        """
        Obtiene el usuario actual a partir del token.
        
        Args:
            token: Access token JWT
            
        Returns:
            Usuario si el token es válido, None si no
        """
        payload = decode_token(token)
        
        if not payload:
            return None
        
        if payload.get("type") != "access":
            return None
        
        user_id = int(payload.get("sub"))
        user = self.user_repo.get_by_id(user_id)
        
        if not user or not user.is_active:
            return None
        
        return user
    
    def _generate_tokens(self, user_id: int) -> Token:
        """
        Genera access y refresh tokens para un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Objeto Token con ambos tokens
        """
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )