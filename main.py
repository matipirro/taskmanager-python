from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import repository as task_repo

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