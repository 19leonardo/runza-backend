"""
MÓDULO: test_ejercicios.py
DESCRIPCIÓN: Pruebas unitarias del módulo de actividades/ejercicios de RunZa
HERRAMIENTA: pytest + FastAPI TestClient
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRegistroEjercicio:
    """Pruebas del endpoint POST /api/v1/activities/exercise"""

    def test_completar_ejercicio_retorna_puntos(self, cliente_autenticado):
        """
        CASO: Usuario autenticado completa un ejercicio válido
        ESPERADO: Retorna puntos ganados y total acumulado
        """
        response = cliente_autenticado.post("/api/v1/activities/exercise", json={
            "name": "Sentadillas",
            "category": "fuerza",
            "duration_seconds": 90,
            "difficulty": "medio",
            "points": 20
        })
        assert response.status_code == 200
        data = response.json()
        assert data["points_earned"] == 20
        assert data["total_points"] >= 20
        assert "message" in data

    def test_ejercicio_sin_category_retorna_422(self, cliente_autenticado):
        """
        CASO: Enviar ejercicio sin el campo 'category'
        ESPERADO: Status 422 - campo requerido por el schema ExerciseCreate
        NOTA: Este fue un bug real encontrado en el proyecto
        """
        response = cliente_autenticado.post("/api/v1/activities/exercise", json={
            "name": "Burpees",
            "duration_seconds": 60,
            "difficulty": "dificil",
            "points": 25
            # falta 'category' - debe dar 422
        })
        assert response.status_code == 422

    def test_multiples_ejercicios_acumulan_puntos(self, cliente_autenticado):
        """
        CASO: Completar 3 ejercicios seguidos
        ESPERADO: Los puntos se acumulan correctamente en la BD
        """
        ejercicios = [
            {"name": "Plancha", "category": "core", "duration_seconds": 60,
             "difficulty": "medio", "points": 15},
            {"name": "Sprints", "category": "cardio", "duration_seconds": 120,
             "difficulty": "dificil", "points": 25},
            {"name": "Estocadas", "category": "fuerza", "duration_seconds": 90,
             "difficulty": "medio", "points": 20},
        ]
        puntos_totales = 0
        for ejercicio in ejercicios:
            r = cliente_autenticado.post("/api/v1/activities/exercise", json=ejercicio)
            assert r.status_code == 200
            puntos_totales += ejercicio["points"]

        # Verificar que los puntos se acumularon en stats
        stats = cliente_autenticado.get("/api/v1/activities/stats")
        assert stats.status_code == 200
        assert stats.json()["total_points"] >= puntos_totales


class TestEstadisticas:
    """Pruebas del endpoint GET /api/v1/activities/stats"""

    def test_stats_usuario_nuevo_inician_en_cero(self, cliente_autenticado):
        """
        CASO: Usuario recién registrado consulta sus estadísticas
        ESPERADO: total_points = 0, total_exercises = 0
        """
        stats = cliente_autenticado.get("/api/v1/activities/stats")
        assert stats.status_code == 200
        data = stats.json()
        assert data["total_points"] == 0
        assert data["total_exercises"] == 0
        assert data["current_streak"] == 0

    def test_stats_contiene_campos_requeridos(self, cliente_autenticado):
        """
        CASO: Verificar que la respuesta tiene todos los campos del schema
        ESPERADO: Todos los campos de UserStatsResponse presentes
        """
        stats = cliente_autenticado.get("/api/v1/activities/stats")
        data = stats.json()
        campos_requeridos = [
            "total_points", "current_streak", "longest_streak",
            "level", "total_exercises", "consistency_score"
        ]
        for campo in campos_requeridos:
            assert campo in data, f"Campo '{campo}' faltante en la respuesta"