import typer
import os
import platform
import asyncio
import string
from datetime import datetime
from rich.console import Console
from sqlmodel import Session, select

from gitauditor.core.catalog import engine, init_db
from gitauditor.core.models import Repo
from gitauditor.core.scanner import GitScanner

console = Console()
catalog_app = typer.Typer(help="Gerenciamento do Catálogo Local de Repositórios")


@catalog_app.command("sync")
def sync_catalog():
    """Varre o sistema e atualiza o catálogo local de repositórios."""
    console.print("[cyan]Inicializando banco de dados local...[/cyan]")
    init_db()

    scanner = GitScanner()
    if platform.system() == "Windows":
        roots = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    else:
        roots = ["/"]

    console.print(
        f"[cyan]Iniciando varredura em {roots} (isso pode levar alguns minutos)...[/cyan]"
    )
    repos_paths = asyncio.run(scanner.scan(roots))

    with Session(engine) as session:
        # Pega todos os caminhos já salvos para identificar orfãos depois (opcional)
        for path in repos_paths:
            repo = session.exec(select(Repo).where(Repo.path == path)).first()
            if not repo:
                repo = Repo(path=path, name=os.path.basename(path))
                session.add(repo)
            else:
                repo.updated_at = datetime.utcnow()

            # Todo (Futuro): Enriquecer chamando um async git_ops extraindo size_mb, remote_url, etc.

        session.commit()

    console.print(
        f"[bold green]✅ Catálogo sincronizado com sucesso![/bold green] {len(repos_paths)} repositórios registrados."
    )


@catalog_app.command("list")
def list_catalog():
    """Lista os repositórios cadastrados no catálogo local."""
    init_db()
    with Session(engine) as session:
        repos = session.exec(select(Repo)).all()
        console.print(
            f"Total: [bold green]{len(repos)}[/bold green] repositórios no catálogo."
        )
        for r in repos:
            console.print(f"- [cyan]{r.name}[/cyan] ({r.path})")
