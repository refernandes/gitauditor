import os
import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Session, create_engine

# Path setup for audit database
HOME_DIR = os.path.expanduser("~")
GITAUDITOR_DIR = os.path.join(HOME_DIR, ".gitauditor")
os.makedirs(GITAUDITOR_DIR, exist_ok=True)
AUDIT_DB_PATH = os.path.join(GITAUDITOR_DIR, "audit.db")

sqlite_url = f"sqlite:///{AUDIT_DB_PATH}"
audit_engine = create_engine(sqlite_url)

class AuditRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    command: str
    repo_path: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    status: str  # "SUCCESS", "ERROR", "WARNING"
    summary: str
    details: Optional[str] = None  # Could be JSON diff, exception trace, or raw output

def init_audit_db():
    SQLModel.metadata.create_all(audit_engine)

class AuditLogger:
    @staticmethod
    def log(
        command: str,
        status: str,
        summary: str,
        repo_path: Optional[str] = None,
        ai_provider: Optional[str] = None,
        ai_model: Optional[str] = None,
        details: Optional[str] = None
    ):
        """Grava uma ação no log de auditoria persistente."""
        try:
            init_audit_db()
            record = AuditRecord(
                command=command,
                status=status,
                summary=summary,
                repo_path=repo_path,
                ai_provider=ai_provider,
                ai_model=ai_model,
                details=details
            )
            with Session(audit_engine) as session:
                session.add(record)
                session.commit()
        except Exception as e:
            # Em falhas de log, não crashamos a aplicação (fail-safe)
            print(f"[AuditLogger Warning] Falha ao gravar log: {e}")
