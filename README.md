# 🏃 RunZa Backend

Backend profesional del ecosistema RunZa - Plataforma integral de fitness con sistema de puntos.

## 🛠️ Stack Tecnológico

- **Framework:** FastAPI 0.109+
- **Base de datos:** PostgreSQL 16
- **ORM:** SQLAlchemy 2.0
- **Migraciones:** Alembic
- **Autenticación:** JWT (python-jose)
- **Validación:** Pydantic V2
- **Testing:** Pytest

## 📁 Estructura del Proyecto
```
runza-backend/
├── app/
│   ├── api/v1/endpoints/    # Endpoints de la API
│   ├── core/                # Configuración central
│   ├── db/                  # Base de datos
│   ├── models/              # Modelos SQLAlchemy
│   ├── schemas/             # Schemas Pydantic
│   ├── services/            # Lógica de negocio
│   ├── repositories/        # Acceso a datos
│   └── utils/               # Utilidades
├── alembic/                 # Migraciones
├── tests/                   # Tests
└── requirements.txt
```

## 🚀 Instalación

### 1. Clonar repositorio
```bash
git clone https://github.com/tu-usuario/runza-backend.git
cd runza-backend
```

### 2. Crear entorno virtual
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus valores
```

### 5. Ejecutar servidor
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentación API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing
```bash
pytest
pytest --cov=app  # Con cobertura
```

## 👨‍💻 Desarrollo
```bash
# Formatear código
black app/
isort app/

# Linting
flake8 app/
```

## 📄 Licencia

Proyecto académico - UNIFRANZ Integrador II

## 👤 Autor

- **Estudiante:** Leonardo Dante Herrera Fernández
- **Materia:** Integrador II
- **Universidad:** UNIFRANZ