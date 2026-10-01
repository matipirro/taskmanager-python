# Task Manager API — FastAPI + SQLAlchemy + Docker Compose + Claude API

REST API para gestión de tareas construida con **Python 3.14 + FastAPI + SQLAlchemy 2.0 + PostgreSQL (Docker Compose) / SQLite (dev local)**, con integración de **Claude API** (Anthropic) para generar y persistir subtareas automáticamente.

[![CI](https://github.com/matipirro/taskmanager-python/actions/workflows/ci.yml/badge.svg)](https://github.com/matipirro/taskmanager-python/actions/workflows/ci.yml)

Proyecto personal desarrollado como práctica de backend moderno en Python siguiendo arquitectura en capas, con suite de tests automatizados con pytest, integración de LLM en el flujo y relaciones 1-a-N con cascade delete.

---

## Stack

- Python 3.14
- FastAPI (OpenAPI/Swagger)
- SQLAlchemy 2.0 (ORM + relaciones 1-a-N + cascade)
- Pydantic 2 (validación JSON)
- PostgreSQL 16 / SQLite
- Uvicorn
- Docker + docker-compose
- pytest + httpx + unittest.mock
- Anthropic SDK + python-dotenv

---

## Endpoints

### Tasks

| Método | Ruta | Descripción |
|---|---|---|
| GET | /health | Health check |
| GET | /tasks | Listar tareas |
| POST | /tasks | Crear tarea |
| GET | /tasks/{id} | Obtener tarea |
| PUT | /tasks/{id} | Actualizar |
| DELETE | /tasks/{id} | Eliminar (cascade a subtasks) |

### Subtasks (generadas por Claude + persistidas)

| Método | Ruta | Descripción |
|---|---|---|
| POST | /tasks/{id}/suggest | Claude Haiku 4.5 genera 3 subtareas y las persiste |
| GET | /tasks/{id}/subtasks | Listar subtareas de una task |
| PUT | /subtasks/{id} | Marcar completada / editar título |

---

## Tests

17 tests con pytest + TestClient + unittest.mock. CI/CD no gasta tokens (mocks).

```bash
pytest -v
```17 passed in 2.42s
---

## Roadmap

- Día 1-5 — Setup + CRUD + SQLAlchemy + capas + tests
- Días 6-8 — Docker + volúmenes
- Día 9 — PostgreSQL + docker-compose (12-Factor)
- Día 10 — GitHub Actions CI/CD
- Día 11 — Integración Claude API
- **Día 12 — Persistencia subtareas + relación 1-a-N + cascade delete + PATCH semantics**
- Días 13-14 — Consolidación y despliegue

---

## Autor

**Matías Pirrone Bruni** · Desarrollador Junior Java & Python · Madrid
- LinkedIn: https://linkedin.com/in/matiaspirrone
- GitHub: https://github.com/matipirro
