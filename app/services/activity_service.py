from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, date
from typing import Optional

from app.models.activity import Activity, ActivityType, DailyStats
from app.models.user import User
from app.schemas.activity import (
    ExerciseCreate, MealCreate, WaterCreate, 
    MoodCreate, SleepCreate, WellnessCreate
)


class ActivityService:
    
    @staticmethod
    def get_or_create_daily_stats(db: Session, user_id: int, target_date: date = None) -> DailyStats:
        """Obtener o crear estadísticas diarias"""
        if target_date is None:
            target_date = date.today()
        
        # Buscar stats del día
        stats = db.query(DailyStats).filter(
            DailyStats.user_id == user_id,
            func.date(DailyStats.date) == target_date
        ).first()
        
        if not stats:
            stats = DailyStats(
                user_id=user_id,
                date=datetime.combine(target_date, datetime.min.time())
            )
            db.add(stats)
            db.commit()
            db.refresh(stats)
        
        return stats

    @staticmethod
    def add_points(db: Session, user_id: int, points: int, point_type: str = "general") -> User:
        """Agregar puntos al usuario y actualizar stats diarios"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Usuario no encontrado")
        
        # Actualizar puntos totales del usuario
        user.total_points += points
        user.last_activity = datetime.utcnow()
        
        # Calcular nivel (cada 500 puntos = 1 nivel)
        user.level = (user.total_points // 500) + 1
        
        # Actualizar stats diarios
        daily_stats = ActivityService.get_or_create_daily_stats(db, user_id)
        daily_stats.total_points += points
        
        if point_type == "exercise":
            daily_stats.exercise_points += points
        elif point_type == "nutrition":
            daily_stats.nutrition_points += points
        elif point_type == "wellness":
            daily_stats.wellness_points += points
        
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def log_exercise(db: Session, user_id: int, data: ExerciseCreate) -> dict:
        """Registrar ejercicio completado"""
        # Crear actividad
        activity = Activity(
            user_id=user_id,
            activity_type=ActivityType.EXERCISE,
            name=data.name,
            category=data.category,
            duration_seconds=data.duration_seconds,
            difficulty=data.difficulty,
            points_earned=data.points
        )
        db.add(activity)
        
        # Actualizar stats diarios
        daily_stats = ActivityService.get_or_create_daily_stats(db, user_id)
        daily_stats.exercises_completed += 1
        
        # Agregar puntos
        user = ActivityService.add_points(db, user_id, data.points, "exercise")
        
        # Actualizar contador total
        user.total_exercises += 1
        
        # Actualizar racha
        ActivityService.update_streak(db, user_id)
        
        db.commit()
        
        return {
            "points_earned": data.points,
            "total_points": user.total_points,
            "message": f"¡Ejercicio completado! +{data.points} puntos"
        }

    @staticmethod
    def log_meal(db: Session, user_id: int, data: MealCreate) -> dict:
        """Registrar comida"""
        points = 10  # Puntos base por registrar comida
        
        activity = Activity(
            user_id=user_id,
            activity_type=ActivityType.MEAL,
            name=data.name,
            category=data.category,
            calories=data.calories,
            protein=data.protein,
            carbs=data.carbs,
            fat=data.fat,
            points_earned=points
        )
        db.add(activity)
        
        # Actualizar stats diarios
        daily_stats = ActivityService.get_or_create_daily_stats(db, user_id)
        daily_stats.meals_logged += 1
        daily_stats.total_calories += data.calories
        daily_stats.total_protein += data.protein
        daily_stats.total_carbs += data.carbs
        daily_stats.total_fat += data.fat
        
        # Agregar puntos
        user = ActivityService.add_points(db, user_id, points, "nutrition")
        user.total_meals_logged += 1
        
        db.commit()
        
        return {
            "points_earned": points,
            "total_points": user.total_points,
            "message": f"¡Comida registrada! +{points} puntos"
        }

    @staticmethod
    def log_water(db: Session, user_id: int, data: WaterCreate) -> dict:
        """Registrar vasos de agua"""
        points = 5 * data.glasses
        
        activity = Activity(
            user_id=user_id,
            activity_type=ActivityType.WATER,
            name=f"{data.glasses} vaso(s) de agua",
            water_glasses=data.glasses,
            points_earned=points
        )
        db.add(activity)
        
        # Actualizar stats diarios
        daily_stats = ActivityService.get_or_create_daily_stats(db, user_id)
        daily_stats.water_glasses += data.glasses
        
        # Agregar puntos
        user = ActivityService.add_points(db, user_id, points, "wellness")
        user.total_water_glasses += data.glasses
        
        db.commit()
        
        return {
            "points_earned": points,
            "total_points": user.total_points,
            "message": f"¡Hidratación registrada! +{points} puntos"
        }

    @staticmethod
    def log_mood(db: Session, user_id: int, data: MoodCreate) -> dict:
        """Registrar estado de ánimo"""
        activity = Activity(
            user_id=user_id,
            activity_type=ActivityType.MOOD,
            name=f"Estado de ánimo: {data.mood}",
            mood_level=data.mood,
            points_earned=data.points
        )
        db.add(activity)
        
        # Actualizar stats diarios
        daily_stats = ActivityService.get_or_create_daily_stats(db, user_id)
        daily_stats.mood = data.mood
        
        # Agregar puntos
        user = ActivityService.add_points(db, user_id, data.points, "wellness")
        
        db.commit()
        
        return {
            "points_earned": data.points,
            "total_points": user.total_points,
            "message": f"¡Estado de ánimo registrado! +{data.points} puntos"
        }

    @staticmethod
    def log_sleep(db: Session, user_id: int, data: SleepCreate) -> dict:
        """Registrar horas de sueño"""
        # Puntos basados en calidad de sueño
        if 7 <= data.hours <= 9:
            points = 20  # Óptimo
        elif 6 <= data.hours < 7 or 9 < data.hours <= 10:
            points = 10  # Aceptable
        else:
            points = 5  # Registrado
        
        activity = Activity(
            user_id=user_id,
            activity_type=ActivityType.SLEEP,
            name=f"Sueño: {data.hours} horas",
            sleep_hours=data.hours,
            points_earned=points
        )
        db.add(activity)
        
        # Actualizar stats diarios
        daily_stats = ActivityService.get_or_create_daily_stats(db, user_id)
        daily_stats.sleep_hours = data.hours
        
        # Agregar puntos
        user = ActivityService.add_points(db, user_id, points, "wellness")
        
        db.commit()
        
        return {
            "points_earned": points,
            "total_points": user.total_points,
            "message": f"¡Sueño registrado! +{points} puntos"
        }

    @staticmethod
    def log_wellness(db: Session, user_id: int, data: WellnessCreate) -> dict:
        """Registrar actividad de bienestar"""
        activity = Activity(
            user_id=user_id,
            activity_type=ActivityType.WELLNESS,
            name=data.name,
            description=data.description,
            duration_seconds=data.duration_minutes * 60 if data.duration_minutes else None,
            points_earned=data.points
        )
        db.add(activity)
        
        # Actualizar stats diarios
        daily_stats = ActivityService.get_or_create_daily_stats(db, user_id)
        daily_stats.wellness_activities += 1
        
        # Agregar puntos
        user = ActivityService.add_points(db, user_id, data.points, "wellness")
        user.total_wellness_activities += 1
        
        db.commit()
        
        return {
            "points_earned": data.points,
            "total_points": user.total_points,
            "message": f"¡{data.name} completado! +{data.points} puntos"
        }

    @staticmethod
    def update_streak(db: Session, user_id: int):
        """Actualizar racha del usuario"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Verificar si hubo actividad ayer
        yesterday_stats = db.query(DailyStats).filter(
            DailyStats.user_id == user_id,
            func.date(DailyStats.date) == yesterday
        ).first()
        
        if yesterday_stats and yesterday_stats.total_points > 0:
            # Mantener o incrementar racha
            user.current_streak += 1
        else:
            # Verificar si es el primer día o se perdió la racha
            today_stats = db.query(DailyStats).filter(
                DailyStats.user_id == user_id,
                func.date(DailyStats.date) == today
            ).first()
            
            if not today_stats or today_stats.total_points == 0:
                # Primera actividad del día, iniciar racha
                user.current_streak = 1
        
        # Actualizar mejor racha
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak
        
        db.commit()

    @staticmethod
    def get_user_stats(db: Session, user_id: int) -> dict:
        """Obtener estadísticas completas del usuario"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Usuario no encontrado")
        
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Puntos esta semana
        week_stats = db.query(func.sum(DailyStats.total_points)).filter(
            DailyStats.user_id == user_id,
            DailyStats.date >= week_ago
        ).scalar() or 0
        
        # Puntos este mes
        month_stats = db.query(func.sum(DailyStats.total_points)).filter(
            DailyStats.user_id == user_id,
            DailyStats.date >= month_ago
        ).scalar() or 0
        
        # Días activos en el último mes
        active_days = db.query(func.count(DailyStats.id)).filter(
            DailyStats.user_id == user_id,
            DailyStats.date >= month_ago,
            DailyStats.total_points > 0
        ).scalar() or 0
        
        # Promedio diario
        avg_daily = month_stats / 30 if month_stats else 0
        
        # Categoría de ejercicio favorita
        favorite_category = db.query(
            Activity.category,
            func.count(Activity.id).label('count')
        ).filter(
            Activity.user_id == user_id,
            Activity.activity_type == ActivityType.EXERCISE,
            Activity.category.isnot(None)
        ).group_by(Activity.category).order_by(desc('count')).first()
        
        # Score de consistencia (días activos / días totales * 100)
        consistency = (active_days / 30) * 100
        
        return {
            "total_points": user.total_points,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "level": user.level,
            "total_exercises": user.total_exercises,
            "total_meals_logged": user.total_meals_logged,
            "total_water_glasses": user.total_water_glasses,
            "total_wellness_activities": user.total_wellness_activities,
            "points_this_week": week_stats,
            "points_this_month": month_stats,
            "average_daily_points": round(avg_daily, 1),
            "favorite_exercise_category": favorite_category[0] if favorite_category else None,
            "consistency_score": round(consistency, 1)
        }

    @staticmethod
    def get_daily_progress(db: Session, user_id: int, days: int = 7) -> list:
        """Obtener progreso de los últimos días"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        
        stats = db.query(DailyStats).filter(
            DailyStats.user_id == user_id,
            func.date(DailyStats.date) >= start_date,
            func.date(DailyStats.date) <= end_date
        ).order_by(DailyStats.date).all()
        
        return stats

    @staticmethod
    def get_recent_activities(db: Session, user_id: int, limit: int = 10) -> list:
        """Obtener actividades recientes"""
        activities = db.query(Activity).filter(
            Activity.user_id == user_id
        ).order_by(desc(Activity.created_at)).limit(limit).all()
        
        return activities