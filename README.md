# Task Manager API — FastAPI + SQLAlchemy + Docker Compose + Claude API

REST API para gestión de tareas construida con **Python 3.14 + FastAPI + SQLAlchemy 2.0 + PostgreSQL (Docker Compose) / SQLite (dev local)**, con integración de **Claude API** (Anthropic) para generar subtareas automáticamente.

[![CI](https://github.com/matipirro/taskmanager-python/actions/workflows/ci.yml/badge.svg)](https://github.com/matipirro/taskmanager-python/actions/workflows/ci.yml)

Proyecto personal desarrollado como práctica de backend moderno en Python siguiendo arquitectura en capas, con suite de tests automatizados con pytest e integración de LLM en el flujo.

---

## 🚀 Stack

- **Python 3.14**
- **FastAPI** — framework web asíncrono, generación automática de OpenAPI/Swagger
- **SQLAlchemy 2.0** — ORM
- **Pydantic 2** — validación de datos y serialización JSON
- **PostgreSQL 16** (Docker Compose) / **SQLite** (dev local) — persistencia
- **Uvicorn** — servidor ASGI
- **Docker + docker-compose** — containerización y orquestación
- **pytest** + **httpx** + **unittest.mock** — testing
- **Anthropic SDK** + **python-dotenv** — integración con Claude API

---

## 📂 Arquitectura

Proyecto organizado en capas para separación clara de responsabilidades:

```
taskmanager-python/
├── main.py # Endpoints HTTP + schemas Pydantic (capa web)
├── repository.py # Operaciones CRUD sobre la BD (capa de datos)
├── models.py # Modelo ORM SQLAlchemy (entidad Task)
├── database.py # Configuración del engine + session (infraestructura)
├── ai_service.py # Integración con Claude API (service layer)
├── test_main.py # Suite de tests con pytest + TestClient + mock
├── requirements.txt # Dependencias del proyecto
└── tasks.db # SQLite (generado en runtime)
```

Equivalente conceptual a Spring Boot:

| Este proyecto (Python) | Spring Boot (Java) |
|---|---|
| `@app.get`, `@app.post` en main.py | `@RestController` + `@GetMapping` |
| `repository.py` | `interface JpaRepository` |
| `models.py` con `Task(Base)` | `@Entity class Task` |
| `database.py` con `SessionLocal` | `DataSource` + `EntityManager` |
| `ai_service.py` | `@Service class AiService` |
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

# 5. Crear .env con tu Anthropic API key (para el endpoint /suggest)
# Ver sección "Integración con Claude API" más abajo
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
| `POST` | `/tasks/{id}/suggest` | 🤖 Sugerir 3 subtareas usando **Claude API** (Anthropic) |

Ejemplo de body para `POST /tasks`:

```json
{
  "title": "Aprender FastAPI",
  "description": "Sprint de Python + FastAPI + SQLAlchemy",
  "completed": false
}
```

---

## 🤖 Integración con Claude API (Anthropic)

El endpoint `POST /tasks/{id}/suggest` usa el modelo **Claude Haiku 4.5** de Anthropic para generar automáticamente 3 subtareas accionables a partir del título y descripción de una tarea existente.

### Configuración

Requiere una variable de entorno con tu API key de Anthropic:

```bash
# .env (NO subir a git — ya está en .gitignore)
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Obtén tu key en [console.anthropic.com](https://console.anthropic.com).

### Ejemplo de uso

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/tasks/1/suggest
```

**Response:**
```json
{
  "task_id": 1,
  "subtasks": [
    "Estudiar la documentación oficial de SQLAlchemy ORM y crear un primer modelo de tabla",
    "Implementar operaciones CRUD (Create, Read, Update, Delete) con una base de datos SQLite de prueba",
    "Practicar consultas avanzadas: filtros, joins y relaciones entre tablas en un proyecto ejemplo"
  ]
}
```

### Arquitectura

- **`ai_service.py`** — módulo aislado que encapsula la llamada a Anthropic (Service Layer pattern)
- **Prompt estructurado** que fuerza a Claude a devolver JSON parseable
- **Manejo de errores**: si Claude devuelve JSON inválido, la API responde `502 Bad Gateway`
- **Coste típico por llamada**: ~$0.001 (Haiku 4.5, ~450 tokens totales)

### Tests

Los tests del endpoint usan `unittest.mock.patch` para simular la respuesta de Claude, evitando llamadas reales a la API en CI/CD:

```python
with patch("ai_service._client.messages.create", return_value=fake_response):
    response = client.post(f"/tasks/{task_id}/suggest")
```

Esto permite que la suite completa corra en **~2 segundos** y **sin gastar tokens**.

---

## 🧪 Tests

Suite de **11 tests** con **pytest** y `TestClient` de FastAPI que cubren:

- Endpoints básicos (`/`, `/health`)
- CRUD completo (POST, GET all, GET by id, PUT, DELETE)
- Códigos de error 404 en operaciones sobre id inexistente
- Test de integración end-to-end (crear → obtener → actualizar → borrar)
- Endpoint `/suggest` con **mock de Claude API** (`unittest.mock`) — happy path, 404 y 502

```bash
pytest -v
```

Salida esperada:
```
11 passed in 2.40s
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

## 🐘 Docker Compose (PostgreSQL + API en 1 comando)

El proyecto incluye `docker-compose.yml` que orquesta la API + PostgreSQL como servicios separados con red interna, volumen persistente y healthcheck.

### Levantar toda la infraestructura

```bash
docker-compose up -d
```

Un solo comando construye la imagen de la API, descarga PostgreSQL 16, crea la red interna, el volumen persistente y arranca ambos servicios en orden (la API espera al healthcheck de la BD).

### Verificar estado

```bash
docker-compose ps
```

Deberías ver 2 servicios `Up`:
- `taskmanager-db` — PostgreSQL 16 (healthy)
- `taskmanager-api` — FastAPI

### Configuración por variables de entorno (12-Factor App)

La conexión a la base de datos se define via `DATABASE_URL`. En `docker-compose.yml` se establece:

```yaml
DATABASE_URL: postgresql://admin:secret@db:5432/tasksdb
```

Cuando la variable no existe (ejecución local sin Docker), el código usa SQLite como fallback:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
```

### Persistencia real

Los datos de PostgreSQL viven en el volumen nombrado `postgres-data`. Los contenedores pueden destruirse y recrearse sin perder información:

```bash
docker-compose down       # destruye contenedores (mantiene volumen)
docker-compose up -d      # recrea, los datos siguen ahí
```

Para borrar TAMBIÉN los datos:

```bash
docker-compose down -v    # -v elimina volúmenes
```

### Inspeccionar la base de datos manualmente

```bash
docker exec -it taskmanager-db psql -U admin -d tasksdb
```

Comandos útiles dentro de `psql`:
- `\dt` — listar tablas
- `SELECT * FROM tasks;` — ver todas las tasks
- `\q` — salir

---

## 🤖 CI/CD (GitHub Actions)

El proyecto tiene un workflow de integración continua que se ejecuta automáticamente en cada `push` a `main` y en cada `pull_request`.

En cada ejecución:

1. Se levanta una máquina virtual Ubuntu efímera
2. Se instala Python 3.13
3. Se instalan las dependencias con `pip install -r requirements.txt`
4. Se ejecuta la suite completa de tests con `pytest -v`

Si algún test falla, el commit queda marcado con una X roja en GitHub y se envía notificación al autor. Los tests del endpoint `/suggest` usan mocks, por lo que **CI/CD no gasta tokens** de la API.

El workflow completo está definido en `.github/workflows/ci.yml`.

---

## 📈 Roadmap

Este proyecto es parte de un sprint personal de aprendizaje de 14 días:

- ✅ Día 1 — Setup Python + venv + FastAPI + primer endpoint
- ✅ Día 2 — CRUD completo con Pydantic + HTTPException
- ✅ Día 3 — SQLAlchemy + SQLite (persistencia real)
- ✅ Día 4 — Arquitectura en capas (repository)
- ✅ Día 5 — Tests con pytest + push a GitHub
- ✅ Días 6-8 — Docker: Dockerfile, .dockerignore, volúmenes para persistencia
- ✅ Día 9 — Migración a PostgreSQL + docker-compose (12-Factor App)
- ✅ Día 10 — GitHub Actions CI/CD (tests automáticos en cada push)
- ✅ Día 11 — Integración Claude API (endpoint `/tasks/{id}/suggest` + tests con mock)
- 🔜 Días 12-14 — Consolidación, mejoras y despliegue

---

## 👤 Autor

**Matías Pirrone Bruni**
Desarrollador Junior Java & Python · Madrid

- LinkedIn: [linkedin.com/in/matiaspirrone](https://linkedin.com/in/matiaspirrone)
- Portfolio: [matipirro.github.io](https://matipirro.github.io)
- GitHub: [github.com/matipirro](https://github.com/matipirro)