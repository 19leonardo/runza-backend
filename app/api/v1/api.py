"""
Router principal de la API v1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, activities

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])