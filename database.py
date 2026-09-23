import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 12-Factor App: la URL viene del entorno.
# Si no se define (dev local), usa SQLite como fallback.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")

# SQLite necesita un argumento especial. PostgreSQL no.
# Detectamos por el prefijo de la URL para no romper con Postgres.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()