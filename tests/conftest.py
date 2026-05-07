import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def usuario_registrado():
    """Registra un usuario de prueba y retorna sus datos"""
    response = client.post("/api/v1/auth/register", json={
        "email": "test_runza@prueba.com",
        "password": "Test1234!",
        "full_name": "Usuario Test"
    })
    return response.json()

@pytest.fixture
def cliente_autenticado(usuario_registrado):
    """Retorna un TestClient con token JWT ya incluido"""
    token = usuario_registrado["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client
    # Limpiar header después del test
    client.headers.pop("Authorization", None)