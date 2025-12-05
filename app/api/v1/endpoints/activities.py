from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.activity_service import ActivityService
from app.schemas.activity import (
    ExerciseCreate, MealCreate, WaterCreate,
    MoodCreate, SleepCreate, WellnessCreate,
    PointsResponse, UserStatsResponse, ActivityResponse
)

router = APIRouter()


@router.post("/exercise", response_model=PointsResponse)
def log_exercise(
    data: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registrar ejercicio completado"""
    result = ActivityService.log_exercise(db, current_user.id, data)
    return result


@router.post("/meal", response_model=PointsResponse)
def log_meal(
    data: MealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registrar comida"""
    result = ActivityService.log_meal(db, current_user.id, data)
    return result


@router.post("/water", response_model=PointsResponse)
def log_water(
    data: WaterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registrar hidratación"""
    result = ActivityService.log_water(db, current_user.id, data)
    return result


@router.post("/mood", response_model=PointsResponse)
def log_mood(
    data: MoodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registrar estado de ánimo"""
    result = ActivityService.log_mood(db, current_user.id, data)
    return result


@router.post("/sleep", response_model=PointsResponse)
def log_sleep(
    data: SleepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registrar horas de sueño"""
    result = ActivityService.log_sleep(db, current_user.id, data)
    return result


@router.post("/wellness", response_model=PointsResponse)
def log_wellness(
    data: WellnessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registrar actividad de bienestar"""
    result = ActivityService.log_wellness(db, current_user.id, data)
    return result


@router.get("/stats", response_model=UserStatsResponse)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas del usuario"""
    stats = ActivityService.get_user_stats(db, current_user.id)
    return stats


@router.get("/progress")
def get_progress(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener progreso de los últimos días"""
    progress = ActivityService.get_daily_progress(db, current_user.id, days)
    return {
        "days": days,
        "progress": [
            {
                "date": stat.date.isoformat(),
                "total_points": stat.total_points,
                "exercises_completed": stat.exercises_completed,
                "meals_logged": stat.meals_logged,
                "water_glasses": stat.water_glasses,
                "mood": stat.mood,
                "sleep_hours": stat.sleep_hours
            }
            for stat in progress
        ]
    }


@router.get("/recent")
def get_recent_activities(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener actividades recientes"""
    activities = ActivityService.get_recent_activities(db, current_user.id, limit)
    return {
        "activities": [
            {
                "id": act.id,
                "type": act.activity_type.value,
                "name": act.name,
                "points": act.points_earned,
                "created_at": act.created_at.isoformat()
            }
            for act in activities
        ]
    }