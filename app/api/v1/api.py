"""
Router principal de la API v1.
Agrupa todos los endpoints de la versión 1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth

api_router = APIRouter()

# Incluir routers de cada módulo
api_router.include_router(auth.router)

# Aquí se agregarán más routers en el futuro:
# api_router.include_router(users.router)
# api_router.include_router(workouts.router)
# api_router.include_router(nutrition.router)
# api_router.include_router(wellness.router)
# api_router.include_router(points.router)
# api_router.include_router(progress.router)