from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class ActivityType(str, enum.Enum):
    EXERCISE = "exercise"
    MEAL = "meal"
    WATER = "water"
    MOOD = "mood"
    SLEEP = "sleep"
    WELLNESS = "wellness"


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    activity_type = Column(Enum(ActivityType), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Datos específicos según tipo
    points_earned = Column(Integer, default=0)
    duration_seconds = Column(Integer, nullable=True)  # Para ejercicios
    calories = Column(Integer, nullable=True)  # Para comidas
    protein = Column(Float, nullable=True)
    carbs = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    water_glasses = Column(Integer, nullable=True)  # Para hidratación
    mood_level = Column(String(50), nullable=True)  # Para estado de ánimo
    sleep_hours = Column(Float, nullable=True)  # Para sueño
    
    # Metadatos
    category = Column(String(50), nullable=True)
    difficulty = Column(String(20), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación con usuario
    user = relationship("User", back_populates="activities")


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Puntos del día
    total_points = Column(Integer, default=0)
    exercise_points = Column(Integer, default=0)
    nutrition_points = Column(Integer, default=0)
    wellness_points = Column(Integer, default=0)
    
    # Contadores
    exercises_completed = Column(Integer, default=0)
    meals_logged = Column(Integer, default=0)
    water_glasses = Column(Integer, default=0)
    
    # Nutrición
    total_calories = Column(Integer, default=0)
    total_protein = Column(Float, default=0)
    total_carbs = Column(Float, default=0)
    total_fat = Column(Float, default=0)
    
    # Bienestar
    mood = Column(String(50), nullable=True)
    sleep_hours = Column(Float, nullable=True)
    wellness_activities = Column(Integer, default=0)
    
    # Racha
    streak_maintained = Column(Integer, default=0)  # 1 si mantuvo racha, 0 si no
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relación
    user = relationship("User", back_populates="daily_stats")