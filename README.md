# Task Manager API — FastAPI + SQLite

REST API para gestión de tareas construida con **Python 3.14 + FastAPI + SQLAlchemy 2.0 + SQLite**.

Proyecto personal desarrollado como práctica de backend moderno en Python siguiendo arquitectura en capas y con suite de tests automatizados con pytest.

---

## 🚀 Stack

- **Python 3.14**
- **FastAPI** — framework web asíncrono, generación automática de OpenAPI/Swagger
- **SQLAlchemy 2.0** — ORM
- **Pydantic 2** — validación de datos y serialización JSON
- **SQLite** — persistencia (base de datos embebida)
- **Uvicorn** — servidor ASGI
- **pytest** + **httpx** — testing

---

## 📂 Arquitectura

Proyecto organizado en capas para separación clara de responsabilidades:

```
taskmanager-python/
├── main.py           # Endpoints HTTP + schemas Pydantic (capa web)
├── repository.py     # Operaciones CRUD sobre la BD (capa de datos)
├── models.py         # Modelo ORM SQLAlchemy (entidad Task)
├── database.py       # Configuración del engine + session (infraestructura)
├── test_main.py      # Suite de tests con pytest + TestClient
├── requirements.txt  # Dependencias del proyecto
└── tasks.db          # SQLite (generado en runtime)
```

Equivalente conceptual a Spring Boot:

| Este proyecto (Python) | Spring Boot (Java) |
|---|---|
| `@app.get`, `@app.post` en main.py | `@RestController` + `@GetMapping` |
| `repository.py` | `interface JpaRepository` |
| `models.py` con `Task(Base)` | `@Entity class Task` |
| `database.py` con `SessionLocal` | `DataSource` + `EntityManager` |
| `Depends(get_db)` | `@Autowired` |

---

## 🔧 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/matipirro/taskmanager-python.git
cd taskmanager-python

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt
```

---

## ▶️ Ejecución

```bash
uvicorn main:app --reload
```

La API estará disponible en:
- **API** → http://127.0.0.1:8000
- **Swagger UI** → http://127.0.0.1:8000/docs
- **ReDoc** → http://127.0.0.1:8000/redoc

---

## 📡 Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Mensaje de bienvenida |
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | Listar todas las tareas |
| `GET` | `/tasks/{id}` | Obtener una tarea por id |
| `POST` | `/tasks` | Crear una nueva tarea |
| `PUT` | `/tasks/{id}` | Actualizar una tarea |
| `DELETE` | `/tasks/{id}` | Eliminar una tarea |

Ejemplo de body para `POST /tasks`:

```json
{
  "title": "Aprender FastAPI",
  "description": "Sprint de Python + FastAPI + SQLAlchemy",
  "completed": false
}
```

---

## 🧪 Tests

Suite de **8 tests** con **pytest** y `TestClient` de FastAPI que cubren:

- Endpoints básicos (`/`, `/health`)
- CRUD completo (POST, GET all, GET by id, PUT, DELETE)
- Códigos de error 404 en operaciones sobre id inexistente
- Test de integración end-to-end (crear → obtener → actualizar → borrar)

```bash
pytest -v
```

Salida esperada:

```
8 passed in 1.09s
```

---

## 🐳 Docker

El proyecto incluye Dockerfile y `.dockerignore` para ejecutar la API en un contenedor sin necesidad de tener Python instalado localmente.

### Construir la imagen

```bash
docker build -t taskmanager-python:v1 .
```

### Ejecutar el contenedor

Con volumen para persistir la base de datos SQLite entre reinicios:

```bash
# Windows PowerShell
docker run -d -p 8000:8000 -v ${PWD}:/app --name taskmanager taskmanager-python:v1

# Linux / Mac
docker run -d -p 8000:8000 -v $(pwd):/app --name taskmanager taskmanager-python:v1
```

La API estará disponible en:
- API → http://localhost:8000
- Swagger UI → http://localhost:8000/docs

### Comandos útiles

```bash
# Ver contenedores corriendo
docker ps

# Ver logs del contenedor
docker logs -f taskmanager

# Parar el contenedor
docker stop taskmanager

# Arrancarlo de nuevo (mantiene datos gracias al volumen)
docker start taskmanager
```

### Arquitectura del contenedor

- Base: `python:3.14-slim` (~150 MB, minimalista)
- Dependencias: instaladas con `pip install --no-cache-dir` para reducir tamaño de imagen
- Bind mount `-v ${PWD}:/app` para persistir `tasks.db` en el host
- Puerto 8000 expuesto para uvicorn

---

## 📈 Roadmap
---

## 📈 Roadmap

Este proyecto es parte de un sprint personal de aprendizaje de 14 días:

- ✅ Día 1 — Setup Python + venv + FastAPI + primer endpoint
- ✅ Día 2 — CRUD completo con Pydantic + HTTPException
- ✅ Día 3 — SQLAlchemy + SQLite (persistencia real)
- ✅ Día 4 — Arquitectura en capas (repository)
- ✅ Día 5 — Tests con pytest + push a GitHub
- ✅ Días 6-8 — Docker: Dockerfile, .dockerignore, volúmenes para persistencia
- 🔜 Días 9-14 — Migración a PostgreSQL + docker-compose + GitHub Actions CI/CD

---

## 👤 Autor

**Matías Pirrone Bruni**
Desarrollador Junior Java & Python · Madrid

- LinkedIn: [linkedin.com/in/matiaspirrone](https://linkedin.com/in/matiaspirrone)
- Portfolio: [matipirro.github.io](https://matipirro.github.io)
- GitHub: [github.com/matipirro](https://github.com/matipirro)