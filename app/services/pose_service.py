"""
Servicio de análisis de poses con MediaPipe.
Detecta poses del cuerpo humano en imágenes.
"""

import mediapipe as mp
import numpy as np
import cv2
import base64
from typing import Optional
from io import BytesIO
from PIL import Image


class PoseService:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def decode_base64_image(self, base64_string: str) -> np.ndarray:
        """Decodificar imagen base64 a numpy array"""
        # Remover el prefijo data:image/...;base64, si existe
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return np.array(image)
    
    def analyze_pose(self, image_base64: str) -> dict:
        """
        Analizar pose en una imagen.
        Retorna landmarks y análisis de la pose.
        """
        try:
            # Decodificar imagen
            image = self.decode_base64_image(image_base64)
            
            # Convertir BGR a RGB (MediaPipe usa RGB)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Procesar con MediaPipe
            results = self.pose.process(image_rgb)
            
            if not results.pose_landmarks:
                return {
                    "success": False,
                    "message": "No se detectó ninguna pose",
                    "landmarks": None,
                    "analysis": None
                }
            
            # Extraer landmarks
            landmarks = []
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                landmarks.append({
                    "id": idx,
                    "name": self.mp_pose.PoseLandmark(idx).name,
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z,
                    "visibility": landmark.visibility
                })
            
            # Analizar pose
            analysis = self._analyze_exercise(landmarks)
            
            return {
                "success": True,
                "message": "Pose detectada correctamente",
                "landmarks": landmarks,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al procesar imagen: {str(e)}",
                "landmarks": None,
                "analysis": None
            }
    
    def _analyze_exercise(self, landmarks: list) -> dict:
        """Analizar la pose para determinar el ejercicio y la forma"""
        
        # Obtener puntos clave
        def get_landmark(name: str):
            for lm in landmarks:
                if lm["name"] == name:
                    return lm
            return None
        
        # Puntos importantes
        left_shoulder = get_landmark("LEFT_SHOULDER")
        right_shoulder = get_landmark("RIGHT_SHOULDER")
        left_elbow = get_landmark("LEFT_ELBOW")
        right_elbow = get_landmark("RIGHT_ELBOW")
        left_wrist = get_landmark("LEFT_WRIST")
        right_wrist = get_landmark("RIGHT_WRIST")
        left_hip = get_landmark("LEFT_HIP")
        right_hip = get_landmark("RIGHT_HIP")
        left_knee = get_landmark("LEFT_KNEE")
        right_knee = get_landmark("RIGHT_KNEE")
        left_ankle = get_landmark("LEFT_ANKLE")
        right_ankle = get_landmark("RIGHT_ANKLE")
        
        analysis = {
            "posture": "unknown",
            "exercise_detected": None,
            "form_score": 0,
            "tips": [],
            "angles": {}
        }
        
        # Calcular ángulos
        if all([left_shoulder, left_elbow, left_wrist]):
            left_arm_angle = self._calculate_angle(
                left_shoulder, left_elbow, left_wrist
            )
            analysis["angles"]["left_arm"] = round(left_arm_angle, 1)
        
        if all([right_shoulder, right_elbow, right_wrist]):
            right_arm_angle = self._calculate_angle(
                right_shoulder, right_elbow, right_wrist
            )
            analysis["angles"]["right_arm"] = round(right_arm_angle, 1)
        
        if all([left_hip, left_knee, left_ankle]):
            left_leg_angle = self._calculate_angle(
                left_hip, left_knee, left_ankle
            )
            analysis["angles"]["left_leg"] = round(left_leg_angle, 1)
        
        if all([right_hip, right_knee, right_ankle]):
            right_leg_angle = self._calculate_angle(
                right_hip, right_knee, right_ankle
            )
            analysis["angles"]["right_leg"] = round(right_leg_angle, 1)
        
        # Detectar tipo de ejercicio basado en la pose
        analysis = self._detect_exercise(analysis, landmarks)
        
        return analysis
    
    def _calculate_angle(self, point1: dict, point2: dict, point3: dict) -> float:
        """Calcular ángulo entre tres puntos"""
        a = np.array([point1["x"], point1["y"]])
        b = np.array([point2["x"], point2["y"]])
        c = np.array([point3["x"], point3["y"]])
        
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
                  np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
        
        return angle
    
    def _detect_exercise(self, analysis: dict, landmarks: list) -> dict:
        """Detectar qué ejercicio está haciendo el usuario"""
        
        angles = analysis.get("angles", {})
        
        # Detectar sentadilla (squats)
        left_leg = angles.get("left_leg", 180)
        right_leg = angles.get("right_leg", 180)
        
        if left_leg < 120 and right_leg < 120:
            analysis["exercise_detected"] = "squat"
            analysis["posture"] = "squat_down"
            
            if left_leg < 90 and right_leg < 90:
                analysis["form_score"] = 100
                analysis["tips"].append("¡Excelente profundidad!")
            elif left_leg < 110 and right_leg < 110:
                analysis["form_score"] = 80
                analysis["tips"].append("Buena forma, intenta bajar un poco más")
            else:
                analysis["form_score"] = 60
                analysis["tips"].append("Intenta bajar más para mejor activación muscular")
        
        # Detectar flexiones (push-ups)
        left_arm = angles.get("left_arm", 180)
        right_arm = angles.get("right_arm", 180)
        
        if left_arm < 100 and right_arm < 100:
            analysis["exercise_detected"] = "pushup"
            analysis["posture"] = "pushup_down"
            analysis["form_score"] = 85
            analysis["tips"].append("Mantén el core apretado")
        
        # Detectar brazos arriba (jumping jacks, etc)
        def get_landmark(name: str):
            for lm in landmarks:
                if lm["name"] == name:
                    return lm
            return None
        
        left_wrist = get_landmark("LEFT_WRIST")
        right_wrist = get_landmark("RIGHT_WRIST")
        left_shoulder = get_landmark("LEFT_SHOULDER")
        right_shoulder = get_landmark("RIGHT_SHOULDER")
        
        if left_wrist and right_wrist and left_shoulder and right_shoulder:
            if left_wrist["y"] < left_shoulder["y"] and right_wrist["y"] < right_shoulder["y"]:
                analysis["exercise_detected"] = "arms_up"
                analysis["posture"] = "standing_arms_up"
                analysis["form_score"] = 90
                analysis["tips"].append("¡Brazos bien arriba!")
        
        # Si no se detectó ejercicio específico
        if not analysis["exercise_detected"]:
            analysis["exercise_detected"] = "standing"
            analysis["posture"] = "neutral"
            analysis["form_score"] = 50
            analysis["tips"].append("Posición neutral detectada")
        
        return analysis


# Instancia global del servicio
pose_service = PoseService()