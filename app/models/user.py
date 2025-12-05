"""
Modelo de Usuario - Tabla principal de usuarios del sistema RunZa.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Perfil
    full_name = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Gamificación
    total_points = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    level = Column(Integer, default=1)
    
    # Estadísticas totales
    total_exercises = Column(Integer, default=0)
    total_meals_logged = Column(Integer, default=0)
    total_water_glasses = Column(Integer, default=0)
    total_wellness_activities = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    daily_stats = relationship("DailyStats", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"