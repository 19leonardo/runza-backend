"""
Punto de entrada principal de la API RunZa.
Configura FastAPI, middlewares, CORS y routers.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import engine, Base

# Importar TODOS los modelos para que SQLAlchemy los registre
from app.models import (
    User, 
    Activity, 
    DailyStats,
    Conversation,
    ConversationParticipant,
    Message
)


def run_migrations():
    """Ejecutar migraciones para tablas nuevas"""
    with engine.connect() as conn:
        try:
            # Agregar columnas nuevas a users si no existen
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='users' AND column_name='is_online') THEN
                        ALTER TABLE users ADD COLUMN is_online BOOLEAN DEFAULT FALSE;
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='users' AND column_name='last_seen') THEN
                        ALTER TABLE users ADD COLUMN last_seen TIMESTAMP WITH TIME ZONE;
                    END IF;
                END $$;
            """))
            conn.commit()
            print("✅ Migraciones ejecutadas correctamente")
        except Exception as e:
            print(f"⚠️ Error en migraciones (puede ser normal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar la app.
    """
    # Startup: Crear tablas si no existen
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos inicializada")
        run_migrations()
    except Exception as e:
        print(f"⚠️ Error inicializando BD: {e}")
    
    yield
    
    # Shutdown
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
    * **Activities** - Registro de actividades
    * **Pose** - Detección de poses
    * **Chat** - Sistema de mensajería
    
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


@app.get("/", tags=["Health"])
async def root():
    """Health check - Verifica que la API está funcionando."""
    return {
        "status": "healthy",
        "message": "🏃 RunZa API is running!",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check detallado para monitoreo."""
    return {
        "status": "healthy",
        "api": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }


# Incluir router de la API v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)