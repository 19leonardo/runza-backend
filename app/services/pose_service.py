"""
Servicio de análisis de poses con MediaPipe.
Detecta poses del cuerpo humano y evalúa ejercicios desde la BD.
"""

import base64
from typing import Optional, List, Dict
from io import BytesIO
from sqlalchemy.orm import Session

from app.models.exercise_detection import (
    ExerciseDetection,
    ExerciseAngleRule,
    ExerciseScoringRule,
    ExerciseTip
)

# NO importar mediapipe al inicio - solo cuando se necesite
MEDIAPIPE_AVAILABLE = False
np = None
Image = None


def _lazy_import():
    """Importar dependencias de forma lazy"""
    global MEDIAPIPE_AVAILABLE, np, Image
    
    try:
        import numpy
        np = numpy
    except ImportError:
        np = None
        return False
    
    try:
        from PIL import Image as PILImage
        Image = PILImage
    except ImportError:
        Image = None
        return False
    
    try:
        import mediapipe
        MEDIAPIPE_AVAILABLE = True
        return True
    except ImportError:
        MEDIAPIPE_AVAILABLE = False
        return False


class PoseService:
    def __init__(self):
        self.pose = None
        self.mp_pose = None
        self._initialized = False

    def _ensure_initialized(self):
        """Inicializar MediaPipe solo cuando se necesite"""
        if self._initialized:
            return
        
        self._initialized = True
        
        if not _lazy_import():
            print("⚠️ No se pudieron importar las dependencias")
            return
        
        if not MEDIAPIPE_AVAILABLE:
            print("⚠️ MediaPipe no disponible")
            return
            
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            print("✅ MediaPipe inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando MediaPipe: {e}")
            self.pose = None

    def decode_base64_image(self, base64_string: str):
        """Decodificar imagen base64 a numpy array"""
        if np is None or Image is None:
            _lazy_import()
        
        if np is None or Image is None:
            return None
            
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))

        if image.mode != 'RGB':
            image = image.convert('RGB')

        return np.array(image)

    def get_exercises_from_db(self, db: Session) -> List[ExerciseDetection]:
        """Obtener todos los ejercicios activos de la BD"""
        try:
            return db.query(ExerciseDetection).filter(
                ExerciseDetection.is_active == True
            ).all()
        except Exception as e:
            print(f"Error obteniendo ejercicios: {e}")
            return []

    def analyze_pose(self, image_base64: str, db: Session = None) -> dict:
        """
        Analizar pose en una imagen.
        Retorna landmarks y análisis de la pose.
        """
        # Inicializar lazy
        self._ensure_initialized()
        
        # Obtener ejercicios de la BD si está disponible
        exercises = []
        if db:
            exercises = self.get_exercises_from_db(db)

        if not MEDIAPIPE_AVAILABLE or self.pose is None:
            return {
                "success": True,
                "message": "Modo demo - MediaPipe no disponible en servidor",
                "landmarks": None,
                "analysis": self._get_demo_analysis(db)
            }

        try:
            image = self.decode_base64_image(image_base64)
            
            if image is None:
                return {
                    "success": False,
                    "message": "Error decodificando imagen",
                    "landmarks": None,
                    "analysis": self._get_demo_analysis(db)
                }
            
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
            print(f"Error en analyze_pose: {e}")
            return {
                "success": False,
                "message": f"Error al procesar imagen: {str(e)}",
                "landmarks": None,
                "analysis": self._get_demo_analysis(db)
            }

    def _get_demo_analysis(self, db: Session = None) -> dict:
        """Retorna un análisis demo cuando MediaPipe no está disponible"""
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
        if np is None:
            return 0.0
            
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

        exercises = self.get_exercises_from_db(db)

        if not exercises:
            return self._fallback_detection(analysis, landmarks, angles)

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
        """Evaluar qué tan bien coincide la pose con un ejercicio."""
        try:
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

                if rule.min_angle <= angle_value <= rule.max_angle:
                    weighted_match += rule.weight
                elif rule.is_required:
                    required_matched = False

                total_weight += rule.weight

            if not required_matched or total_weight == 0:
                return 0, 0

            match_score = weighted_match / total_weight
            form_score = self._calculate_form_score(exercise.id, angles, db)

            return match_score, form_score
        except Exception as e:
            print(f"Error evaluando ejercicio: {e}")
            return 0, 0

    def _calculate_form_score(self, exercise_id: int, angles: dict, db: Session) -> int:
        """Calcular puntuación de forma basada en reglas de scoring"""
        try:
            scoring_rules = db.query(ExerciseScoringRule).filter(
                ExerciseScoringRule.exercise_id == exercise_id
            ).all()

            if not scoring_rules:
                return 75

            total_score = 0
            rules_count = 0

            for rule in scoring_rules:
                angle_value = angles.get(rule.angle_name)
                
                if angle_value is None:
                    continue

                rules_count += 1

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
        except Exception as e:
            print(f"Error calculando form score: {e}")
            return 75

    def _get_tips_for_score(self, exercise_id: int, score: int, db: Session) -> List[str]:
        """Obtener tips apropiados para el score obtenido"""
        try:
            tips = db.query(ExerciseTip).filter(
                ExerciseTip.exercise_id == exercise_id,
                ExerciseTip.score_min <= score,
                ExerciseTip.score_max >= score
            ).order_by(ExerciseTip.priority).limit(3).all()

            return [tip.tip_text for tip in tips]
        except Exception as e:
            print(f"Error obteniendo tips: {e}")
            return ["Mantén buena postura"]

    def _fallback_detection(self, analysis: dict, landmarks: list, angles: dict) -> dict:
        """Detección fallback cuando no hay BD disponible"""
        
        left_knee = angles.get("left_knee", 180)
        right_knee = angles.get("right_knee", 180)

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

        analysis["exercise_detected"] = "standing"
        analysis["exercise_display_name"] = "Posición Neutral"
        analysis["posture"] = "neutral"
        analysis["form_score"] = 50
        analysis["tips"].append("Posición neutral detectada")

        return analysis


# Crear instancia global (no inicializa MediaPipe hasta que se use)
pose_service = PoseService()