"""
Configuración central de la aplicación RunZa.
Utiliza Pydantic Settings para validación de variables de entorno.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración de la aplicación cargada desde variables de entorno.
    Pydantic valida automáticamente los tipos y valores.
    """
    
    # Configuración general
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "RunZa API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Base de datos
    DATABASE_URL: str
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:8081,http://localhost:19006"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convierte string de orígenes a lista."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def is_development(self) -> bool:
        """Verifica si está en modo desarrollo."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Verifica si está en modo producción."""
        return self.ENVIRONMENT == "production"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instancia cacheada de Settings.
    Usar lru_cache evita leer el .env en cada request.
    """
    return Settings()


# Instancia global para imports directos
settings = get_settings()