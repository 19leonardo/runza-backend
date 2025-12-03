"""
Repositorio de Usuario - Capa de acceso a datos.
Maneja todas las operaciones CRUD de usuarios en la base de datos.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """
    Repositorio para operaciones de base de datos relacionadas con usuarios.
    Implementa el patrón Repository para separar lógica de acceso a datos.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa el repositorio con una sesión de base de datos.
        
        Args:
            db: Sesión de SQLAlchemy
        """
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario si existe, None si no
        """
        return self.db.get(User, user_id)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario si existe, None si no
        """
        stmt = select(User).where(User.email == email.lower())
        return self.db.execute(stmt).scalar_one_or_none()
    
    def create(self, user_data: dict) -> User:
        """
        Crea un nuevo usuario en la base de datos.
        
        Args:
            user_data: Diccionario con datos del usuario
            
        Returns:
            Usuario creado
        """
        # Asegurar que el email esté en minúsculas
        if "email" in user_data:
            user_data["email"] = user_data["email"].lower()
        
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user: User, update_data: dict) -> User:
        """
        Actualiza los datos de un usuario existente.
        
        Args:
            user: Usuario a actualizar
            update_data: Diccionario con datos a actualizar
            
        Returns:
            Usuario actualizado
        """
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_last_login(self, user: User) -> User:
        """
        Actualiza la fecha del último login.
        
        Args:
            user: Usuario que hizo login
            
        Returns:
            Usuario actualizado
        """
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user: User) -> bool:
        """
        Elimina un usuario de la base de datos.
        
        Args:
            user: Usuario a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        self.db.delete(user)
        self.db.commit()
        return True
    
    def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email: Email a verificar
            
        Returns:
            True si existe, False si no
        """
        stmt = select(User.id).where(User.email == email.lower())
        result = self.db.execute(stmt).scalar_one_or_none()
        return result is not None