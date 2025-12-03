"""
Configuración de SQLAlchemy y sesión de base de datos.
Implementa patrón de sesión con dependency injection para FastAPI.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings


# Crear engine de SQLAlchemy
# pool_pre_ping=True verifica conexiones antes de usarlas (evita errores de conexión caída)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG  # Muestra queries SQL en desarrollo
)

# Factory de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    """
    Clase base para todos los modelos SQLAlchemy.
    Todos los modelos heredan de esta clase.
    """
    pass


def get_db() -> Generator[Session, None, None]:
    """
    Dependency que provee sesión de base de datos.
    Se usa con Depends() en los endpoints de FastAPI.
    
    Yields:
        Session: Sesión de SQLAlchemy
        
    Example:
        @router.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()