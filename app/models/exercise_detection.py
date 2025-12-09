"""
Modelos para detección de ejercicios con parámetros escalables.
Los parámetros de cada ejercicio se guardan en la BD.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class ExerciseDetection(Base):
    """Tabla principal de ejercicios detectables"""
    __tablename__ = "exercise_detections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    sport = Column(String(50), default="general")
    difficulty = Column(String(20), default="medium")
    is_active = Column(Boolean, default=True)
    icon = Column(String(50), default="fitness")
    color = Column(String(20), default="#6366F1")

    angle_rules = relationship("ExerciseAngleRule", back_populates="exercise", cascade="all, delete-orphan")
    scoring_rules = relationship("ExerciseScoringRule", back_populates="exercise", cascade="all, delete-orphan")
    tips = relationship("ExerciseTip", back_populates="exercise", cascade="all, delete-orphan")


class ExerciseAngleRule(Base):
    """Reglas de ángulos para detectar cada ejercicio"""
    __tablename__ = "exercise_angle_rules"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercise_detections.id"), nullable=False)
    angle_name = Column(String(50), nullable=False)
    min_angle = Column(Float, nullable=False)
    max_angle = Column(Float, nullable=False)
    phase = Column(String(20), default="any")
    weight = Column(Float, default=1.0)
    is_required = Column(Boolean, default=True)

    exercise = relationship("ExerciseDetection", back_populates="angle_rules")


class ExerciseScoringRule(Base):
    """Reglas de puntuación basadas en ángulos"""
    __tablename__ = "exercise_scoring_rules"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercise_detections.id"), nullable=False)
    angle_name = Column(String(50), nullable=False)
    excellent_min = Column(Float, nullable=False)
    excellent_max = Column(Float, nullable=False)
    good_min = Column(Float, nullable=False)
    good_max = Column(Float, nullable=False)
    acceptable_min = Column(Float, nullable=False)
    acceptable_max = Column(Float, nullable=False)

    exercise = relationship("ExerciseDetection", back_populates="scoring_rules")


class ExerciseTip(Base):
    """Tips/consejos según la puntuación obtenida"""
    __tablename__ = "exercise_tips"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercise_detections.id"), nullable=False)
    score_min = Column(Integer, default=0)
    score_max = Column(Integer, default=100)
    tip_text = Column(String(255), nullable=False)
    priority = Column(Integer, default=1)

    exercise = relationship("ExerciseDetection", back_populates="tips")