from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# URL de conexión — para SQLite es "sqlite:///./nombre.db"
# Los 3 slashes: 2 del protocolo + 1 de "ruta relativa" (./)
DATABASE_URL = "sqlite:///./tasks.db"

# El engine — sabe cómo hablar con SQLite
# connect_args solo lo necesita SQLite (para permitir usarlo desde múltiples hilos)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Fábrica de sesiones — cada request abrirá una desde aquí
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredarán nuestros modelos (Task)
Base = declarative_base()

# Dependencia para FastAPI: abre sesión, la entrega, la cierra al terminar
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()