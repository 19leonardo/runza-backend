"""
Schemas para análisis de poses.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class PoseAnalysisRequest(BaseModel):
    """Request para analizar una pose"""
    image_base64: str


class LandmarkResponse(BaseModel):
    """Respuesta de un landmark"""
    id: int
    name: str
    x: float
    y: float
    z: float
    visibility: float


class AnalysisResponse(BaseModel):
    """Respuesta del análisis"""
    posture: str
    exercise_detected: Optional[str]
    form_score: int
    tips: List[str]
    angles: Dict[str, float]


class PoseAnalysisResponse(BaseModel):
    """Respuesta completa del análisis de pose"""
    success: bool
    message: str
    landmarks: Optional[List[Dict[str, Any]]]
    analysis: Optional[Dict[str, Any]]