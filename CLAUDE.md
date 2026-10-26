# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API locally (SQLite fallback, no Docker needed)
uvicorn main:app --reload

# Run all tests
pytest -v

# Run a single test
pytest -v test_main.py::test_flujo_completo_crud

# Run with PostgreSQL via Docker
docker-compose up --build
```

The API docs are available at `http://localhost:8000/docs` (Swagger UI) when running.

## Environment

Copy `.env` and set `ANTHROPIC_API_KEY` for the AI endpoint to work. The database defaults to SQLite (`tasks.db`) if `DATABASE_URL` is not set. For PostgreSQL, set `DATABASE_URL=postgresql://admin:secret@localhost:5432/tasksdb` and start the container with `docker-compose up db`.

## Architecture

The project follows a strict 3-layer separation:

- **`main.py`** — FastAPI app, all endpoints, all Pydantic schemas. No SQLAlchemy here.
- **`repository.py`** — All DB queries (SQLAlchemy). Endpoints never touch SQLAlchemy directly.
- **`models.py`** — SQLAlchemy ORM models (`Task`, `Subtask`). Tables are created at startup via `Base.metadata.create_all`.
- **`database.py`** — Engine + session factory. Detects SQLite vs PostgreSQL via URL prefix to apply the right `connect_args`.
- **`ai_service.py`** — Anthropic SDK wrapper. `suggest_subtasks()` calls Claude Haiku 4.5 and parses JSON; strips markdown code fences if present. Raises `ValueError` on invalid JSON (surfaced as 502 in the endpoint).

### Data model

`Task` (1) → (N) `Subtask` with `cascade="all, delete-orphan"`. Deleting a Task cascades to its Subtasks both at the ORM level and via `ondelete="CASCADE"` on the FK.

### AI flow

`POST /tasks/{id}/suggest` → fetches task from DB → calls `ai_service.suggest_subtasks()` → persists returned titles as `Subtask` rows via `repository.create_subtasks()` → returns `SuggestResponse`.

### Tests

Tests run against an in-memory SQLite DB via `TestClient(app)`. Claude API calls are mocked via `unittest.mock.patch("ai_service._client.messages.create", ...)`. The mock helper `_mock_claude_response(json_text)` is defined in `test_main.py`. CI runs `pytest -v` on every push/PR to `main`.

## Convenciones del usuario

- **Modo aprendizaje:** antes de implementar código nuevo, explicar el concepto brevemente y hacer 2-3 preguntas de quiz para confirmar comprensión antes de empezar a escribir.
- **Credenciales:** nunca modificar `.env` ni commitear credenciales. Verificar que `.env` esté en `.gitignore` antes de cualquier commit.
- **Tests y commits:** siempre correr `pytest -v` antes de proponer un commit. Nunca hacer `git commit` sin aprobación explícita del usuario.
- **Base de datos:** nunca borrar `tasks.db` sin pedir confirmación explícita.
- **Entorno virtual:** verificar que el venv esté activo (el prompt muestra `(venv)`) antes de ejecutar comandos Python o pip.
- **Modelo preferido:** `claude-haiku-4-5` para integraciones con Claude API (barato y rápido).
- **Idioma:** comentarios en español, nombres de variables y funciones en inglés.
- **Respuestas:** concisas con bullets, no párrafos largos.
