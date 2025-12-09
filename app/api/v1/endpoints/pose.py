"""
Endpoints para análisis de poses con MediaPipe.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.pose import PoseAnalysisRequest, PoseAnalysisResponse
from app.services.pose_service import pose_service

router = APIRouter()


@router.post("/analyze", response_model=PoseAnalysisResponse)
async def analyze_pose(
    request: PoseAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analizar pose en una imagen base64.
    Detecta ejercicios y evalúa la forma usando reglas de la BD.
    """
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="Se requiere una imagen en base64")

    result = pose_service.analyze_pose(request.image_base64, db)

    return result


@router.get("/health")
async def pose_health(db: Session = Depends(get_db)):
    """Verificar estado del servicio de poses"""
    from app.services.pose_service import MEDIAPIPE_AVAILABLE
    from app.models.exercise_detection import ExerciseDetection

    # Contar ejercicios en la BD
    exercise_count = db.query(ExerciseDetection).filter(
        ExerciseDetection.is_active == True
    ).count()

    # Obtener nombres de ejercicios
    exercises = db.query(ExerciseDetection).filter(
        ExerciseDetection.is_active == True
    ).all()
    exercise_names = [e.display_name for e in exercises]

    return {
        "status": "healthy",
        "mediapipe_available": MEDIAPIPE_AVAILABLE,
        "exercises_loaded": exercise_count,
        "exercises": exercise_names,
        "message": "Servicio de análisis de poses funcionando correctamente"
    }


@router.get("/exercises")
async def get_available_exercises(db: Session = Depends(get_db)):
    """Obtener lista de ejercicios disponibles para detección"""
    from app.models.exercise_detection import ExerciseDetection

    exercises = db.query(ExerciseDetection).filter(
        ExerciseDetection.is_active == True
    ).all()

    return {
        "success": True,
        "count": len(exercises),
        "exercises": [
            {
                "name": e.name,
                "display_name": e.display_name,
                "description": e.description,
                "category": e.category,
                "sport": e.sport,
                "difficulty": e.difficulty,
                "icon": e.icon,
                "color": e.color
            }
            for e in exercises
        ]
    }