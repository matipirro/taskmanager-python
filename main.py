from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import repository as task_repo
from ai_service import suggest_subtasks as ai_suggest_subtasks

# Crea las tablas la primera vez que arranca
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Task Manager API",
    description=(
        "REST API para gestión de tareas con **integración de Claude API** (Anthropic) "
        "para generar y persistir subtareas automáticamente.\n\n"
        "**Stack:** FastAPI · SQLAlchemy 2.0 · PostgreSQL (docker-compose) / SQLite · "
        "Anthropic SDK · pytest · Docker · CI/CD con GitHub Actions.\n\n"
        "**Repo:** [github.com/matipirro/taskmanager-python](https://github.com/matipirro/taskmanager-python)"
    ),
    version="0.4.0",
    contact={
        "name": "Matías Pirrone",
        "url": "https://linkedin.com/in/matiaspirrone",
        "email": "matipn02@gmail.com",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "General",
            "description": "Endpoints de bienvenida y health check.",
        },
        {
            "name": "Tasks",
            "description": "CRUD completo de tareas. Al eliminar una Task se eliminan sus Subtasks por cascade.",
        },
        {
            "name": "AI",
            "description": "Generación de subtareas con Claude Haiku 4.5 (Anthropic). Las subtareas generadas se persisten en la BD.",
        },
        {
            "name": "Subtasks",
            "description": "Gestión de subtareas asociadas a Tasks: listado y actualización parcial (PATCH semantics con `exclude_unset`).",
        },
    ],
)

# ---------- Pydantic schemas ----------
# IMPORTANTE: añadimos import de Field al top del archivo
# (si no está ya) — ver línea 2

class TaskCreate(BaseModel):
    """Body para crear o actualizar una Task."""
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Título de la tarea. Obligatorio, entre 1 y 200 caracteres.",
        examples=["Preparar presentación para el cliente"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Descripción opcional de la tarea (hasta 2000 caracteres).",
        examples=["Reunión programada para el jueves. Incluir métricas Q3."],
    )
    completed: bool = Field(
        default=False,
        description="Estado de completado. False por defecto.",
    )

    # Rechaza campos extra que no estén declarados aquí (seguridad + bugs silenciosos)
    model_config = ConfigDict(extra="forbid")


class TaskResponse(BaseModel):
    """Representación de una Task tal como se devuelve en respuestas."""
    id: int
    title: str
    description: str | None
    completed: bool

    model_config = ConfigDict(from_attributes=True)


class SubtaskResponse(BaseModel):
    """Representación de una Subtask tal como se devuelve en respuestas."""
    id: int
    title: str
    completed: bool
    task_id: int

    model_config = ConfigDict(from_attributes=True)


class SubtaskUpdate(BaseModel):
    """
    Body para actualizar una Subtask.
    Todos los campos son opcionales — solo se actualizan los enviados (PATCH semantics).
    """
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Nuevo título. Si no se envía, se mantiene el actual.",
        examples=["Revisar sección de métricas"],
    )
    completed: bool | None = Field(
        default=None,
        description="Nuevo estado completado. Si no se envía, se mantiene el actual.",
        examples=[True],
    )

    model_config = ConfigDict(extra="forbid")


class SuggestResponse(BaseModel):
    """Respuesta del endpoint /suggest: subtareas generadas por Claude y ya persistidas en BD."""
    task_id: int
    subtasks: list[SubtaskResponse]

# ---------- Endpoints ----------
@app.get("/", tags=["General"])
def home():
    return {"mensaje": "¡Task Manager API v0.4 — con subtareas AI persistidas! 🚀"}

@app.get("/health", tags=["General"])
def health():
    return {"status": "ok"}

@app.post("/tasks", response_model=TaskResponse, tags=["Tasks"], status_code=201)
def crear_task(task: TaskCreate, db: Session = Depends(get_db)):
    return task_repo.create_task(db, task.model_dump())

@app.get("/tasks", response_model=list[TaskResponse], tags=["Tasks"])
def listar_tasks(db: Session = Depends(get_db)):
    return task_repo.get_all_tasks(db)

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def obtener_task(task_id: int, db: Session = Depends(get_db)):
    task = task_repo.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} no encontrada")
    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def actualizar_task(task_id: int, task_actualizada: TaskCreate, db: Session = Depends(get_db)):
    task = task_repo.update_task(db, task_id, task_actualizada.model_dump())
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} no encontrada")
    return task

@app.delete("/tasks/{task_id}", tags=["Tasks"])
def borrar_task(task_id: int, db: Session = Depends(get_db)):
    if not task_repo.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail=f"Task {task_id} no encontrada")
    return {"mensaje": f"Task {task_id} eliminada"}
@app.post("/tasks/{task_id}/suggest", response_model=SuggestResponse, tags=["AI"])
def sugerir_subtasks(task_id: int, db: Session = Depends(get_db)):
    """
    Usa Claude para sugerir 3 subtareas a partir de una tarea existente
    y las persiste en la BD asociadas a la task padre.
    """
    task = task_repo.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} no encontrada")

    try:
        titles = ai_suggest_subtasks(task.title, task.description)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Error de IA: {e}") from e

    # Persistir las subtareas en la BD
    saved_subtasks = task_repo.create_subtasks(db, task_id=task_id, titles=titles)

    return {"task_id": task_id, "subtasks": saved_subtasks}

# ---------- Endpoints de Subtasks ----------

@app.get("/tasks/{task_id}/subtasks", response_model=list[SubtaskResponse], tags=["Subtasks"])
def listar_subtasks(task_id: int, db: Session = Depends(get_db)):
    """Devuelve todas las subtareas de una task."""
    task = task_repo.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} no encontrada")
    return task_repo.get_subtasks_by_task(db, task_id)


@app.put("/subtasks/{subtask_id}", response_model=SubtaskResponse, tags=["Subtasks"])
def actualizar_subtask(subtask_id: int, subtask_actualizada: SubtaskUpdate, db: Session = Depends(get_db)):
    """Actualiza una subtarea (marcar completada, cambiar título)."""
    # exclude_unset=True: solo actualizamos los campos que el cliente envió
    update_data = subtask_actualizada.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

    subtask = task_repo.update_subtask(db, subtask_id, update_data)
    if subtask is None:
        raise HTTPException(status_code=404, detail=f"Subtask {subtask_id} no encontrada")
    return subtask