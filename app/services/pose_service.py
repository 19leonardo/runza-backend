"""
Servicio de análisis de poses con MediaPipe.
Detecta poses del cuerpo humano y evalúa ejercicios desde la BD.
"""

import base64
import numpy as np
from typing import Optional, List, Dict
from io import BytesIO
from PIL import Image
from sqlalchemy.orm import Session

from app.models.exercise_detection import (
    ExerciseDetection,
    ExerciseAngleRule,
    ExerciseScoringRule,
    ExerciseTip
)

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

    def get_exercises_from_db(self, db: Session) -> List[ExerciseDetection]:
        """Obtener todos los ejercicios activos de la BD"""
        return db.query(ExerciseDetection).filter(
            ExerciseDetection.is_active == True
        ).all()

    def analyze_pose(self, image_base64: str, db: Session = None) -> dict:
        """
        Analizar pose en una imagen.
        Retorna landmarks y análisis de la pose.
        """
        # Obtener ejercicios de la BD si está disponible
        exercises = []
        if db:
            exercises = self.get_exercises_from_db(db)

        if not MEDIAPIPE_AVAILABLE or self.pose is None:
            return {
                "success": False,
                "message": "MediaPipe no está disponible en este servidor",
                "landmarks": None,
                "analysis": self._get_demo_analysis(db)
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
                        "exercise_display_name": None,
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

            analysis = self._analyze_exercise_from_db(landmarks, db)

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

    def _get_demo_analysis(self, db: Session = None) -> dict:
        """Retorna un análisis demo cuando MediaPipe no está disponible"""
        # Obtener ejercicios de la BD para el demo
        exercises_info = []
        if db:
            exercises = self.get_exercises_from_db(db)
            exercises_info = [{"name": e.name, "display_name": e.display_name} for e in exercises]

        return {
            "posture": "demo_mode",
            "exercise_detected": "demo",
            "exercise_display_name": "Modo Demo",
            "form_score": 85,
            "tips": [
                "Modo demo activo",
                "El análisis real requiere MediaPipe",
                "Mantén buena postura durante el ejercicio"
            ],
            "angles": {
                "left_knee": 90.0,
                "right_knee": 90.0,
                "left_hip": 170.0,
                "right_hip": 170.0,
                "left_arm": 90.0,
                "right_arm": 90.0
            },
            "available_exercises": exercises_info
        }

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

    def _get_landmark(self, landmarks: list, name: str) -> Optional[dict]:
        """Obtener un landmark por nombre"""
        for lm in landmarks:
            if lm["name"] == name:
                return lm
        return None

    def _calculate_all_angles(self, landmarks: list) -> dict:
        """Calcular todos los ángulos relevantes del cuerpo"""
        angles = {}

        # Definir los puntos para cada ángulo
        angle_definitions = {
            "left_arm": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"),
            "right_arm": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"),
            "left_knee": ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"),
            "right_knee": ("RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE"),
            "left_hip": ("LEFT_SHOULDER", "LEFT_HIP", "LEFT_KNEE"),
            "right_hip": ("RIGHT_SHOULDER", "RIGHT_HIP", "RIGHT_KNEE"),
            "left_hip_knee": ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"),
            "right_hip_knee": ("RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE"),
            "left_shoulder": ("LEFT_ELBOW", "LEFT_SHOULDER", "LEFT_HIP"),
            "right_shoulder": ("RIGHT_ELBOW", "RIGHT_SHOULDER", "RIGHT_HIP"),
        }

        for angle_name, (p1_name, p2_name, p3_name) in angle_definitions.items():
            p1 = self._get_landmark(landmarks, p1_name)
            p2 = self._get_landmark(landmarks, p2_name)
            p3 = self._get_landmark(landmarks, p3_name)

            if all([p1, p2, p3]):
                angle = self._calculate_angle(p1, p2, p3)
                angles[angle_name] = round(angle, 1)

        return angles

    def _analyze_exercise_from_db(self, landmarks: list, db: Session) -> dict:
        """Analizar ejercicio usando reglas de la base de datos"""
        
        # Calcular todos los ángulos
        angles = self._calculate_all_angles(landmarks)

        analysis = {
            "posture": "unknown",
            "exercise_detected": None,
            "exercise_display_name": None,
            "form_score": 0,
            "tips": [],
            "angles": angles
        }

        if not db:
            return self._fallback_detection(analysis, landmarks, angles)

        # Obtener ejercicios de la BD
        exercises = self.get_exercises_from_db(db)

        if not exercises:
            return self._fallback_detection(analysis, landmarks, angles)

        # Evaluar cada ejercicio
        best_match = None
        best_score = 0

        for exercise in exercises:
            match_score, form_score = self._evaluate_exercise(exercise, angles, db)
            
            if match_score > best_score and match_score >= 0.5:
                best_score = match_score
                best_match = {
                    "exercise": exercise,
                    "form_score": form_score,
                    "match_score": match_score
                }

        if best_match:
            exercise = best_match["exercise"]
            form_score = best_match["form_score"]

            # Obtener tips según el score
            tips = self._get_tips_for_score(exercise.id, form_score, db)

            analysis["exercise_detected"] = exercise.name
            analysis["exercise_display_name"] = exercise.display_name
            analysis["posture"] = f"{exercise.name}_detected"
            analysis["form_score"] = form_score
            analysis["tips"] = tips
            analysis["category"] = exercise.category
            analysis["sport"] = exercise.sport
        else:
            analysis["posture"] = "neutral"
            analysis["exercise_detected"] = "standing"
            analysis["exercise_display_name"] = "Posición Neutral"
            analysis["form_score"] = 50
            analysis["tips"] = ["Posición neutral detectada. Realiza un ejercicio para analizar tu forma."]

        return analysis

    def _evaluate_exercise(self, exercise: ExerciseDetection, angles: dict, db: Session) -> tuple:
        """
        Evaluar qué tan bien coincide la pose con un ejercicio.
        Retorna (match_score, form_score)
        """
        # Obtener reglas de ángulos
        angle_rules = db.query(ExerciseAngleRule).filter(
            ExerciseAngleRule.exercise_id == exercise.id
        ).all()

        if not angle_rules:
            return 0, 0

        total_weight = 0
        weighted_match = 0
        required_matched = True

        for rule in angle_rules:
            angle_value = angles.get(rule.angle_name)
            
            if angle_value is None:
                if rule.is_required:
                    required_matched = False
                continue

            # Verificar si el ángulo está en el rango
            if rule.min_angle <= angle_value <= rule.max_angle:
                weighted_match += rule.weight
            elif rule.is_required:
                required_matched = False

            total_weight += rule.weight

        if not required_matched or total_weight == 0:
            return 0, 0

        match_score = weighted_match / total_weight

        # Calcular form_score basado en las reglas de puntuación
        form_score = self._calculate_form_score(exercise.id, angles, db)

        return match_score, form_score

    def _calculate_form_score(self, exercise_id: int, angles: dict, db: Session) -> int:
        """Calcular puntuación de forma basada en reglas de scoring"""
        scoring_rules = db.query(ExerciseScoringRule).filter(
            ExerciseScoringRule.exercise_id == exercise_id
        ).all()

        if not scoring_rules:
            return 75  # Score por defecto

        total_score = 0
        rules_count = 0

        for rule in scoring_rules:
            angle_value = angles.get(rule.angle_name)
            
            if angle_value is None:
                continue

            rules_count += 1

            # Evaluar en qué rango cae el ángulo
            if rule.excellent_min <= angle_value <= rule.excellent_max:
                total_score += 100
            elif rule.good_min <= angle_value <= rule.good_max:
                total_score += 80
            elif rule.acceptable_min <= angle_value <= rule.acceptable_max:
                total_score += 60
            else:
                total_score += 40

        if rules_count == 0:
            return 75

        return int(total_score / rules_count)

    def _get_tips_for_score(self, exercise_id: int, score: int, db: Session) -> List[str]:
        """Obtener tips apropiados para el score obtenido"""
        tips = db.query(ExerciseTip).filter(
            ExerciseTip.exercise_id == exercise_id,
            ExerciseTip.score_min <= score,
            ExerciseTip.score_max >= score
        ).order_by(ExerciseTip.priority).limit(3).all()

        return [tip.tip_text for tip in tips]

    def _fallback_detection(self, analysis: dict, landmarks: list, angles: dict) -> dict:
        """Detección fallback cuando no hay BD disponible"""
        
        left_knee = angles.get("left_knee", 180)
        right_knee = angles.get("right_knee", 180)
        left_arm = angles.get("left_arm", 180)
        right_arm = angles.get("right_arm", 180)

        # Detectar sentadilla
        if left_knee < 120 and right_knee < 120:
            analysis["exercise_detected"] = "sentadillas"
            analysis["exercise_display_name"] = "Sentadillas"
            analysis["posture"] = "squat_down"
            
            if left_knee < 90 and right_knee < 90:
                analysis["form_score"] = 100
                analysis["tips"].append("¡Excelente profundidad!")
            elif left_knee < 110 and right_knee < 110:
                analysis["form_score"] = 80
                analysis["tips"].append("Buena forma, intenta bajar un poco más")
            else:
                analysis["form_score"] = 60
                analysis["tips"].append("Intenta bajar más para mejor activación")
            return analysis

        # Detectar polichinelas (brazos arriba)
        left_wrist = self._get_landmark(landmarks, "LEFT_WRIST")
        right_wrist = self._get_landmark(landmarks, "RIGHT_WRIST")
        left_shoulder = self._get_landmark(landmarks, "LEFT_SHOULDER")
        right_shoulder = self._get_landmark(landmarks, "RIGHT_SHOULDER")

        if all([left_wrist, right_wrist, left_shoulder, right_shoulder]):
            if left_wrist["y"] < left_shoulder["y"] and right_wrist["y"] < right_shoulder["y"]:
                analysis["exercise_detected"] = "polichinelas"
                analysis["exercise_display_name"] = "Polichinelas"
                analysis["posture"] = "jumping_jack_up"
                analysis["form_score"] = 85
                analysis["tips"].append("¡Brazos bien arriba! Mantén el ritmo.")
                return analysis

        # Detectar skipping (rodilla alta)
        left_hip = self._get_landmark(landmarks, "LEFT_HIP")
        right_hip = self._get_landmark(landmarks, "RIGHT_HIP")
        left_knee_lm = self._get_landmark(landmarks, "LEFT_KNEE")
        right_knee_lm = self._get_landmark(landmarks, "RIGHT_KNEE")

        if all([left_hip, right_hip, left_knee_lm, right_knee_lm]):
            # Si una rodilla está significativamente más alta que la cadera
            if left_knee_lm["y"] < left_hip["y"] - 0.05 or right_knee_lm["y"] < right_hip["y"] - 0.05:
                analysis["exercise_detected"] = "skipping"
                analysis["exercise_display_name"] = "Skipping Alto"
                analysis["posture"] = "high_knees"
                analysis["form_score"] = 80
                analysis["tips"].append("¡Buena altura de rodillas!")
                return analysis

        # Posición neutral
        analysis["exercise_detected"] = "standing"
        analysis["exercise_display_name"] = "Posición Neutral"
        analysis["posture"] = "neutral"
        analysis["form_score"] = 50
        analysis["tips"].append("Posición neutral detectada")

        return analysis


pose_service = PoseService()