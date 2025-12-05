from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    EXERCISE = "exercise"
    MEAL = "meal"
    WATER = "water"
    MOOD = "mood"
    SLEEP = "sleep"
    WELLNESS = "wellness"


# === Schemas para crear actividades ===

class ExerciseCreate(BaseModel):
    name: str
    category: str
    duration_seconds: int
    difficulty: Optional[str] = None
    points: int


class MealCreate(BaseModel):
    name: str
    category: str  # desayuno, almuerzo, cena, snack
    calories: int
    protein: float
    carbs: float
    fat: float


class WaterCreate(BaseModel):
    glasses: int = 1


class MoodCreate(BaseModel):
    mood: str  # amazing, happy, good, neutral, tired, stressed, sad
    points: int


class SleepCreate(BaseModel):
    hours: float


class WellnessCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    points: int


# === Schemas de respuesta ===

class ActivityResponse(BaseModel):
    id: int
    activity_type: str
    name: str
    points_earned: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PointsResponse(BaseModel):
    points_earned: int
    total_points: int
    message: str


class DailyStatsResponse(BaseModel):
    date: datetime
    total_points: int
    exercise_points: int
    nutrition_points: int
    wellness_points: int
    exercises_completed: int
    meals_logged: int
    water_glasses: int
    total_calories: int
    mood: Optional[str]
    sleep_hours: Optional[float]
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    total_points: int
    current_streak: int
    longest_streak: int
    level: int
    total_exercises: int
    total_meals_logged: int
    total_water_glasses: int
    total_wellness_activities: int
    
    # Estadísticas calculadas
    points_this_week: int
    points_this_month: int
    average_daily_points: float
    favorite_exercise_category: Optional[str]
    consistency_score: float  # 0-100


class ProgressResponse(BaseModel):
    daily_stats: list[DailyStatsResponse]
    weekly_summary: dict
    monthly_summary: dict
    achievements: list[dict]