from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)

    # Relación 1-a-N: una Task tiene muchas Subtasks
    # cascade="all, delete-orphan" -> borrar Task borra sus Subtasks
    subtasks = relationship(
        "Subtask",
        back_populates="task",
        cascade="all, delete-orphan",
    )


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)

    # Foreign Key: apunta a tasks.id
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)

    # Relación inversa: cada Subtask sabe a qué Task pertenece
    task = relationship("Task", back_populates="subtasks")