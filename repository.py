"""
Capa de acceso a datos (Repository).
Todas las operaciones SQL sobre Task viven aquí.
Los endpoints NO tocan SQLAlchemy directamente — solo llaman a estas funciones.
"""

from sqlalchemy.orm import Session
from models import Task as TaskModel


def get_all_tasks(db: Session):
    """SELECT * FROM tasks"""
    return db.query(TaskModel).all()


def get_task_by_id(db: Session, task_id: int):
    """SELECT * FROM tasks WHERE id = ? LIMIT 1"""
    return db.query(TaskModel).filter(TaskModel.id == task_id).first()


def create_task(db: Session, task_data: dict):
    """INSERT INTO tasks (...) VALUES (...)"""
    new_task = TaskModel(**task_data)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


def update_task(db: Session, task_id: int, task_data: dict):
    """UPDATE tasks SET ... WHERE id = ?"""
    task = get_task_by_id(db, task_id)
    if task is None:
        return None
    for key, value in task_data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int):
    """DELETE FROM tasks WHERE id = ?"""
    task = get_task_by_id(db, task_id)
    if task is None:
        return False
    db.delete(task)
    db.commit()
    return True