"""
Script para insertar los ejercicios de detección en la base de datos.
Ejercicios específicos para entrenamiento de futbolistas.
"""

from sqlalchemy.orm import Session
from app.models.exercise_detection import (
    ExerciseDetection,
    ExerciseAngleRule,
    ExerciseScoringRule,
    ExerciseTip
)


def seed_football_exercises(db: Session):
    """Insertar ejercicios de fútbol en la base de datos"""
    
    # Verificar si ya existen ejercicios
    existing = db.query(ExerciseDetection).first()
    if existing:
        print("Los ejercicios ya están insertados")
        return
    
    # ============================================
    # EJERCICIO 1: SKIPPING (Rodillas Altas)
    # ============================================
    skipping = ExerciseDetection(
        name="skipping",
        display_name="Skipping Alto",
        description="Carrera con rodillas altas. Fundamental para la coordinación y potencia en futbolistas.",
        category="pliometria",
        sport="futbol",
        difficulty="medium",
        is_active=True,
        icon="walk",
        color="#10B981"
    )
    db.add(skipping)
    db.flush()  # Para obtener el ID
    
    # Reglas de ángulos para Skipping
    # La rodilla debe subir alto (ángulo de cadera-rodilla pequeño)
    skipping_angles = [
        ExerciseAngleRule(
            exercise_id=skipping.id,
            angle_name="left_hip_knee",
            min_angle=30,
            max_angle=90,
            phase="up",
            weight=1.0,
            is_required=True
        ),
        ExerciseAngleRule(
            exercise_id=skipping.id,
            angle_name="right_hip_knee",
            min_angle=30,
            max_angle=90,
            phase="up",
            weight=1.0,
            is_required=True
        ),
        ExerciseAngleRule(
            exercise_id=skipping.id,
            angle_name="left_knee",
            min_angle=60,
            max_angle=120,
            phase="up",
            weight=0.8,
            is_required=False
        ),
        ExerciseAngleRule(
            exercise_id=skipping.id,
            angle_name="right_knee",
            min_angle=60,
            max_angle=120,
            phase="up",
            weight=0.8,
            is_required=False
        )
    ]
    db.add_all(skipping_angles)
    
    # Reglas de puntuación para Skipping
    skipping_scoring = ExerciseScoringRule(
        exercise_id=skipping.id,
        angle_name="left_hip_knee",
        excellent_min=30,
        excellent_max=50,
        good_min=50,
        good_max=70,
        acceptable_min=70,
        acceptable_max=90
    )
    db.add(skipping_scoring)
    
    # Tips para Skipping
    skipping_tips = [
        ExerciseTip(exercise_id=skipping.id, score_min=90, score_max=100, tip_text="¡Excelente altura de rodillas! Mantén el ritmo.", priority=1),
        ExerciseTip(exercise_id=skipping.id, score_min=70, score_max=89, tip_text="Buena forma. Intenta subir las rodillas un poco más.", priority=1),
        ExerciseTip(exercise_id=skipping.id, score_min=50, score_max=69, tip_text="Sube más las rodillas, deben llegar a la altura de la cadera.", priority=1),
        ExerciseTip(exercise_id=skipping.id, score_min=0, score_max=49, tip_text="Las rodillas deben subir mucho más. Practica el movimiento lentamente.", priority=1),
        ExerciseTip(exercise_id=skipping.id, score_min=0, score_max=100, tip_text="Mantén el core activado y la espalda recta.", priority=2),
        ExerciseTip(exercise_id=skipping.id, score_min=0, score_max=100, tip_text="Los brazos deben moverse en coordinación con las piernas.", priority=3)
    ]
    db.add_all(skipping_tips)
    
    # ============================================
    # EJERCICIO 2: POLICHINELAS (Jumping Jacks)
    # ============================================
    polichinelas = ExerciseDetection(
        name="polichinelas",
        display_name="Polichinelas",
        description="Jumping Jacks. Ejercicio cardiovascular que mejora la coordinación y resistencia.",
        category="cardio",
        sport="futbol",
        difficulty="easy",
        is_active=True,
        icon="body",
        color="#F59E0B"
    )
    db.add(polichinelas)
    db.flush()
    
    # Reglas de ángulos para Polichinelas
    # Brazos arriba y piernas separadas
    polichinelas_angles = [
        ExerciseAngleRule(
            exercise_id=polichinelas.id,
            angle_name="left_arm",
            min_angle=150,
            max_angle=180,
            phase="up",
            weight=1.0,
            is_required=True
        ),
        ExerciseAngleRule(
            exercise_id=polichinelas.id,
            angle_name="right_arm",
            min_angle=150,
            max_angle=180,
            phase="up",
            weight=1.0,
            is_required=True
        ),
        ExerciseAngleRule(
            exercise_id=polichinelas.id,
            angle_name="legs_spread",
            min_angle=30,
            max_angle=60,
            phase="up",
            weight=0.8,
            is_required=False
        )
    ]
    db.add_all(polichinelas_angles)
    
    # Reglas de puntuación para Polichinelas
    polichinelas_scoring = ExerciseScoringRule(
        exercise_id=polichinelas.id,
        angle_name="left_arm",
        excellent_min=165,
        excellent_max=180,
        good_min=150,
        good_max=165,
        acceptable_min=130,
        acceptable_max=150
    )
    db.add(polichinelas_scoring)
    
    # Tips para Polichinelas
    polichinelas_tips = [
        ExerciseTip(exercise_id=polichinelas.id, score_min=90, score_max=100, tip_text="¡Perfecta extensión! Brazos y piernas bien coordinados.", priority=1),
        ExerciseTip(exercise_id=polichinelas.id, score_min=70, score_max=89, tip_text="Buena forma. Extiende los brazos completamente hacia arriba.", priority=1),
        ExerciseTip(exercise_id=polichinelas.id, score_min=50, score_max=69, tip_text="Intenta extender más los brazos y separar más las piernas.", priority=1),
        ExerciseTip(exercise_id=polichinelas.id, score_min=0, score_max=49, tip_text="Los brazos deben llegar completamente arriba, sobre la cabeza.", priority=1),
        ExerciseTip(exercise_id=polichinelas.id, score_min=0, score_max=100, tip_text="Mantén un ritmo constante durante todo el ejercicio.", priority=2),
        ExerciseTip(exercise_id=polichinelas.id, score_min=0, score_max=100, tip_text="Aterriza suavemente para proteger tus rodillas.", priority=3)
    ]
    db.add_all(polichinelas_tips)
    
    # ============================================
    # EJERCICIO 3: SENTADILLAS
    # ============================================
    sentadillas = ExerciseDetection(
        name="sentadillas",
        display_name="Sentadillas",
        description="Ejercicio fundamental para fortalecer piernas y glúteos. Esencial para la potencia en el fútbol.",
        category="fuerza",
        sport="futbol",
        difficulty="medium",
        is_active=True,
        icon="fitness",
        color="#6366F1"
    )
    db.add(sentadillas)
    db.flush()
    
    # Reglas de ángulos para Sentadillas
    sentadillas_angles = [
        ExerciseAngleRule(
            exercise_id=sentadillas.id,
            angle_name="left_knee",
            min_angle=70,
            max_angle=120,
            phase="down",
            weight=1.0,
            is_required=True
        ),
        ExerciseAngleRule(
            exercise_id=sentadillas.id,
            angle_name="right_knee",
            min_angle=70,
            max_angle=120,
            phase="down",
            weight=1.0,
            is_required=True
        ),
        ExerciseAngleRule(
            exercise_id=sentadillas.id,
            angle_name="left_hip",
            min_angle=70,
            max_angle=120,
            phase="down",
            weight=0.9,
            is_required=True
        ),
        ExerciseAngleRule(
            exercise_id=sentadillas.id,
            angle_name="right_hip",
            min_angle=70,
            max_angle=120,
            phase="down",
            weight=0.9,
            is_required=True
        )
    ]
    db.add_all(sentadillas_angles)
    
    # Reglas de puntuación para Sentadillas
    sentadillas_scoring = ExerciseScoringRule(
        exercise_id=sentadillas.id,
        angle_name="left_knee",
        excellent_min=70,
        excellent_max=90,
        good_min=90,
        good_max=105,
        acceptable_min=105,
        acceptable_max=120
    )
    db.add(sentadillas_scoring)
    
    # Tips para Sentadillas
    sentadillas_tips = [
        ExerciseTip(exercise_id=sentadillas.id, score_min=90, score_max=100, tip_text="¡Excelente profundidad! Sentadilla perfecta.", priority=1),
        ExerciseTip(exercise_id=sentadillas.id, score_min=70, score_max=89, tip_text="Buena forma. Intenta bajar un poco más.", priority=1),
        ExerciseTip(exercise_id=sentadillas.id, score_min=50, score_max=69, tip_text="Baja más para activar mejor los glúteos.", priority=1),
        ExerciseTip(exercise_id=sentadillas.id, score_min=0, score_max=49, tip_text="La sentadilla debe ser más profunda. Los muslos deben quedar paralelos al suelo.", priority=1),
        ExerciseTip(exercise_id=sentadillas.id, score_min=0, score_max=100, tip_text="Mantén la espalda recta y el pecho hacia arriba.", priority=2),
        ExerciseTip(exercise_id=sentadillas.id, score_min=0, score_max=100, tip_text="Las rodillas no deben pasar la punta de los pies.", priority=3),
        ExerciseTip(exercise_id=sentadillas.id, score_min=0, score_max=100, tip_text="Empuja desde los talones al subir.", priority=4)
    ]
    db.add_all(sentadillas_tips)
    
    # Guardar todo
    db.commit()
    print("✅ Ejercicios de fútbol insertados correctamente:")
    print("   - Skipping Alto")
    print("   - Polichinelas")
    print("   - Sentadillas")


def clear_exercises(db: Session):
    """Eliminar todos los ejercicios (para desarrollo)"""
    db.query(ExerciseTip).delete()
    db.query(ExerciseScoringRule).delete()
    db.query(ExerciseAngleRule).delete()
    db.query(ExerciseDetection).delete()
    db.commit()
    print("🗑️ Todos los ejercicios eliminados")