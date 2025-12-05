"""
Servicio de análisis de poses con MediaPipe.
Detecta poses del cuerpo humano en imágenes.
"""

import base64
import numpy as np
from typing import Optional
from io import BytesIO
from PIL import Image

# Importar mediapipe de forma segura
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


class PoseService:
    def __init__(self):
        self.pose = None
        self.mp_pose = None
        
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_pose = mp.solutions.pose
                self.pose = self.mp_pose.Pose(
                    static_image_mode=True,
                    model_complexity=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            except Exception as e:
                print(f"Error inicializando MediaPipe: {e}")
                self.pose = None
    
    def decode_base64_image(self, base64_string: str) -> np.ndarray:
        """Decodificar imagen base64 a numpy array"""
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return np.array(image)
    
    def analyze_pose(self, image_base64: str) -> dict:
        """
        Analizar pose en una imagen.
        Retorna landmarks y análisis de la pose.
        """
        if not MEDIAPIPE_AVAILABLE or self.pose is None:
            return {
                "success": False,
                "message": "MediaPipe no está disponible en este servidor",
                "landmarks": None,
                "analysis": self._get_demo_analysis()
            }
        
        try:
            image = self.decode_base64_image(image_base64)
            results = self.pose.process(image)
            
            if not results.pose_landmarks:
                return {
                    "success": True,
                    "message": "No se detectó ninguna pose en la imagen",
                    "landmarks": None,
                    "analysis": {
                        "posture": "not_detected",
                        "exercise_detected": None,
                        "form_score": 0,
                        "tips": ["Asegúrate de que tu cuerpo completo sea visible en la cámara"],
                        "angles": {}
                    }
                }
            
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
    
    def _get_demo_analysis(self) -> dict:
        """Retorna un análisis demo cuando MediaPipe no está disponible"""
        return {
            "posture": "demo_mode",
            "exercise_detected": "demo",
            "form_score": 85,
            "tips": [
                "Modo demo activo",
                "El análisis real requiere MediaPipe",
                "Mantén buena postura durante el ejercicio"
            ],
            "angles": {
                "left_arm": 90.0,
                "right_arm": 90.0,
                "left_leg": 170.0,
                "right_leg": 170.0
            }
        }
    
    def _analyze_exercise(self, landmarks: list) -> dict:
        """Analizar la pose para determinar el ejercicio y la forma"""
        
        def get_landmark(name: str):
            for lm in landmarks:
                if lm["name"] == name:
                    return lm
            return None
        
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
                analysis["tips"].append("Intenta bajar más para mejor activación")
            return analysis
        
        left_arm = angles.get("left_arm", 180)
        right_arm = angles.get("right_arm", 180)
        
        if left_arm < 100 and right_arm < 100:
            analysis["exercise_detected"] = "pushup"
            analysis["posture"] = "pushup_down"
            analysis["form_score"] = 85
            analysis["tips"].append("Mantén el core apretado")
            return analysis
        
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
                return analysis
        
        analysis["exercise_detected"] = "standing"
        analysis["posture"] = "neutral"
        analysis["form_score"] = 50
        analysis["tips"].append("Posición neutral detectada")
        
        return analysis


pose_service = PoseService()