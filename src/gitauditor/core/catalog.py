import os
from sqlmodel import create_engine, Session, SQLModel

# Importa para registrar no metadata do SQLModel

DB_DIR = os.path.expanduser("~/.gitauditor")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "catalog.db")
sqlite_url = f"sqlite:///{DB_PATH}"

# Usando connect_args={"check_same_thread": False} se precisarmos compartilhar conexões,
# mas para comandos do CLI, uma conexão padrão é suficiente.
engine = create_engine(sqlite_url)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
