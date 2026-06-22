from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Repo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    host: Optional[str] = Field(default=None, index=True)  # Ex: github.com, gitlab.com
    owner: Optional[str] = Field(default=None, index=True)  # Ex: refernandes
    canonical_name: Optional[str] = Field(
        default=None, index=True
    )  # Ex: github.com/refernandes/gitauditor

    # Metadados enriquecidos
    tags: Optional[str] = Field(default="")  # Separados por vírgula ou JSON string
    size_mb: Optional[float] = Field(default=0.0)

    # Saúde do Repositório
    remote_url: Optional[str] = Field(default=None)
    status: str = Field(default="Unknown")  # OK, Local, Stale, Broken, Timeout
    last_activity: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # P3: Semantic Fields
    ai_summary: Optional[str] = Field(default=None)
    ai_tags: Optional[str] = Field(default=None)  # CSV format
    ai_stack: Optional[str] = Field(default=None)
    ai_risk: Optional[str] = Field(default=None)

    # P3: Governance Fields
    ai_model: Optional[str] = Field(default=None)
    ai_prompt_version: Optional[str] = Field(default=None)
    ai_updated_at: Optional[datetime] = Field(default=None)
    ai_confidence: Optional[float] = Field(default=None)
    ai_error: Optional[str] = Field(default=None)
    ai_source_hash: Optional[str] = Field(default=None)
