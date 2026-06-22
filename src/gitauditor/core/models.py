from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Repo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    host: Optional[str] = Field(default=None, index=True)  # Ex: github.com, gitlab.com
    owner: Optional[str] = Field(default=None, index=True)  # Ex: refernandes

    # Metadados enriquecidos
    tags: Optional[str] = Field(default="")  # Separados por vírgula ou JSON string
    size_mb: Optional[float] = Field(default=0.0)

    # Saúde do Repositório
    remote_url: Optional[str] = Field(default=None)
    status: str = Field(default="Unknown")  # OK, Local, Stale, Broken, Timeout
    last_activity: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
