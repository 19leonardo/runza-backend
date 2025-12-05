"""
Endpoints para análisis de poses.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.pose_service import pose_service
from app.schemas.pose import PoseAnalysisRequest, PoseAnalysisResponse

router = APIRouter()


@router.post("/analyze", response_model=PoseAnalysisResponse)
async def analyze_pose(
    request: PoseAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analizar pose en una imagen.
    Recibe imagen en base64 y retorna landmarks y análisis.
    """
    result = pose_service.analyze_pose(request.image_base64)
    return result


@router.get("/health")
async def pose_health():
    """Verificar que el servicio de poses está funcionando"""
    return {
        "status": "ok",
        "service": "pose_analysis",
        "message": "MediaPipe está listo"
    }