"""
MÓDULO: test_chat.py
DESCRIPCIÓN: Pruebas unitarias del sistema de chat de RunZa
HERRAMIENTA: pytest + FastAPI TestClient
NOTA: Este módulo tuvo un bug real (comparación de datetimes) detectado en producción
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestContactos:
    """Pruebas del sistema de contactos del chat"""

    def test_obtener_contactos_lista_vacia_usuario_nuevo(self, cliente_autenticado):
        """
        CASO: Usuario nuevo sin contactos consulta su lista
        ESPERADO: Status 200 con lista vacía
        """
        response = cliente_autenticado.get("/api/v1/chat/contacts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

    def test_agregar_contacto_email_inexistente_retorna_404(self, cliente_autenticado):
        """
        CASO: Intentar agregar un contacto que no existe en la BD
        ESPERADO: Status 404 Not Found
        """
        response = cliente_autenticado.post("/api/v1/chat/contacts", json={
            "email": "usuario_que_no_existe@runza.com"
        })
        assert response.status_code == 404

    def test_agregar_contacto_valido(self, cliente_autenticado):
        """
        CASO: Agregar un usuario que SÍ existe como contacto
        ESPERADO: Status 200 y datos del contacto agregado
        SETUP: Primero registramos un segundo usuario
        """
        # Crear segundo usuario
        client.post("/api/v1/auth/register", json={
            "email": "contacto2@runza.com",
            "password": "Test1234!",
            "full_name": "Segundo Usuario"
        })

        response = cliente_autenticado.post("/api/v1/chat/contacts", json={
            "email": "contacto2@runza.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "contacto2@runza.com"

    def test_contactos_retorna_200_sin_error_datetime(self, cliente_autenticado):
        """
        CASO: Bug real corregido — TypeError comparación offset-naive vs offset-aware
        ESPERADO: Status 200 (antes retornaba 500 Internal Server Error)
        CAUSA ORIGINAL: datetime.min sin timezone vs datetime con timezone en sort()
        SOLUCIÓN: Normalizar con .replace(tzinfo=timezone.utc) antes de comparar
        """
        response = cliente_autenticado.get("/api/v1/chat/contacts")
        assert response.status_code == 200  # No debe ser 500


class TestBusqueda:
    """Pruebas del endpoint de búsqueda de usuarios"""

    def test_buscar_usuario_existente(self, cliente_autenticado):
        """
        CASO: Buscar un usuario por email parcial
        ESPERADO: Lista con al menos un resultado
        """
        # Crear usuario para buscar
        client.post("/api/v1/auth/register", json={
            "email": "buscable@runza.com",
            "password": "Test1234!",
            "full_name": "Usuario Buscable"
        })

        response = cliente_autenticado.get("/api/v1/chat/search?q=buscable")
        assert response.status_code == 200
        resultados = response.json()
        assert len(resultados) >= 1
        assert any(u["email"] == "buscable@runza.com" for u in resultados)

    def test_buscar_sin_query_retorna_422(self, cliente_autenticado):
        """
        CASO: Llamar al endpoint de búsqueda sin parámetro 'q'
        ESPERADO: Status 422 - parámetro requerido
        """
        response = cliente_autenticado.get("/api/v1/chat/search")
        assert response.status_code == 422