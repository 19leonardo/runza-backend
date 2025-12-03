"""
Punto de entrada principal de la API RunZa.
Configura FastAPI, middlewares, CORS y routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import engine, Base

# Importar modelos para que SQLAlchemy los registre
from app.models.user import User  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar la app.
    """
    # Startup: Crear tablas si no existen (solo desarrollo)
    if settings.is_development:
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos inicializada (modo desarrollo)")
    
    yield
    
    # Shutdown: Limpieza si es necesaria
    print("👋 Cerrando aplicación RunZa API")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## RunZa API - Backend del Ecosistema RunZa
    
    API RESTful para la plataforma de fitness RunZa.
    
    ### Módulos:
    * **Auth** - Autenticación y registro de usuarios
    * **Users** - Gestión de perfiles de usuario
    * **Workouts** - Entrenamientos y ejercicios
    * **Nutrition** - Registro nutricional
    * **Wellness** - Estado de ánimo e hidratación
    * **Points** - Sistema de puntos y recompensas
    * **Progress** - Análisis y estadísticas
    
    ### Documentación:
    * Swagger UI: `/docs`
    * ReDoc: `/redoc`
    """,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint (raíz)
@app.get("/", tags=["Health"])
async def root():
    """
    Health check - Verifica que la API está funcionando.
    """
    return {
        "status": "healthy",
        "message": "🏃 RunZa API is running!",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check detallado para monitoreo.
    """
    return {
        "status": "healthy",
        "api": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }


# Incluir router de la API v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)   