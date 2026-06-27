import os

from sqlmodel import Session, SQLModel, create_engine

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

    # Heurística simples de Migration:
    # Se uma nova versão adicionou colunas que não existem, o select vai falhar.
    # Como o banco é de cache efêmero, fazemos um Drop & Recreate para evitar crashs.
    from sqlalchemy.exc import OperationalError
    from sqlmodel import Session, select

    from gitauditor.core.models import Repo

    try:
        with Session(engine) as session:
            session.exec(select(Repo).limit(1)).first()
    except OperationalError as e:
        if "no such column" in str(e).lower() or "table" in str(e).lower():
            # Schema mudou, refaz o cache do zero
            SQLModel.metadata.drop_all(engine)
            SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
