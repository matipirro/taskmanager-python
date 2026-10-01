from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import repository as task_repo
from ai_service import suggest_subtasks as ai_suggest_subtasks

# Crea las tablas la primera vez que arranca
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Task Manager API",
    description="API REST en Python + FastAPI + SQLite (arquitectura en capas)",
    version="0.3.0"
)

# ---------- Pydantic schemas ----------
class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    completed: bool = False

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool

    model_config = ConfigDict(from_attributes=True)

class SubtaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    task_id: int

    model_config = ConfigDict(from_attributes=True)


class SubtaskUpdate(BaseModel):
    """Body para actualizar una subtask (marcar completada o cambiar título)."""
    title: str | None = None
    completed: bool | None = None


class SuggestResponse(BaseModel):
    """Respuesta del endpoint /suggest: devuelve las subtareas ya persistidas."""
    task_id: int
    subtasks: list[SubtaskResponse]

# ---------- Endpoints ----------
@app.get("/")
def home():
    return {"mensaje": "¡Task Manager API v0.3 — con capa de repository! 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/tasks", response_model=TaskResponse)
def crear_task(task: TaskCreate, db: Session = Depends(get_db)):
    return task_repo.create_task(db, task.model_dump())

@app.get("/tasks", response_model=list[TaskResponse])
def listar_tasks(db: Session = Depends(get_db)):
    return task_repo.get_all_tasks(db)

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def obtener_task(task_id: int, db: Session = Depends(get_db)):
    task = task_repo.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} no encontrada")
    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def actualizar_task(task_id: int, task_actualizada: TaskCreate, db: Session = Depends(get_db)):
    task = task_repo.update_task(db, task_id, task_actualizada.model_dump())
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} no encontrada")
    return task

@app.delete("/tasks/{task_id}")
def borrar_task(task_id: int, db: Session = Depends(get_db)):
    if not task_repo.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail=f"Task {task_id} no encontrada")
    return {"mensaje": f"Task {task_id} eliminada"}

@app.post("/tasks/{task_id}/suggest", response_model=SuggestResponse)
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

@app.get("/tasks/{task_id}/subtasks", response_model=list[SubtaskResponse])
def listar_subtasks(task_id: int, db: Session = Depends(get_db)):
    """Devuelve todas las subtareas de una task."""
    task = task_repo.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} no encontrada")
    return task_repo.get_subtasks_by_task(db, task_id)


@app.put("/subtasks/{subtask_id}", response_model=SubtaskResponse)
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