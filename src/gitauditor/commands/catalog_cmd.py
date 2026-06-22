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
from gitauditor.core.enricher import enrich_all
from rich.table import Table

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

    console.print(
        "[cyan]Enriquecendo metadados (identificando remotes e owners)...[/cyan]"
    )
    enriched_data = asyncio.run(enrich_all(repos_paths))

    with Session(engine) as session:
        for data in enriched_data:
            repo = session.exec(select(Repo).where(Repo.path == data["path"])).first()
            if not repo:
                repo = Repo(path=data["path"], name=os.path.basename(data["path"]))
                session.add(repo)

            repo.remote_url = data["remote_url"]
            repo.host = data["host"]
            repo.owner = data["owner"]
            repo.canonical_name = data["canonical_name"]
            repo.status = data["status"]
            repo.updated_at = datetime.utcnow()

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


@catalog_app.command("health")
def health_dashboard():
    """Mostra um dashboard da saúde dos repositórios no catálogo."""
    init_db()
    with Session(engine) as session:
        repos = session.exec(select(Repo)).all()
        if not repos:
            console.print(
                "[yellow]O catálogo está vazio. Rode `gitauditor catalog sync`.[/yellow]"
            )
            return

        orphans = [r for r in repos if r.status == "Orphan"]

        table = Table(title="📊 Dashboard de Saúde do Catálogo")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="magenta")

        table.add_row("Total de Repositórios", str(len(repos)))
        table.add_row("Órfãos (Sem origin)", str(len(orphans)))

        # Check canonical dupes
        canonical_map = {}
        for r in repos:
            if r.canonical_name:
                canonical_map.setdefault(r.canonical_name, []).append(r)

        duplicados = [c for c, reps in canonical_map.items() if len(reps) > 1]
        table.add_row("Projetos Duplicados", str(len(duplicados)))

        console.print(table)


@catalog_app.command("dedupe")
def dedupe_repos(
    plan: bool = typer.Option(
        False, "--plan", help="Mostra apenas o plano de deduplicação"
    ),
):
    """Identifica e propõe a normalização de repositórios duplicados lógicos."""
    init_db()
    with Session(engine) as session:
        repos = session.exec(select(Repo)).all()
        canonical_map = {}
        for r in repos:
            if r.canonical_name:
                canonical_map.setdefault(r.canonical_name, []).append(r)

        duplicados = {c: reps for c, reps in canonical_map.items() if len(reps) > 1}

        if not duplicados:
            console.print(
                "[green]✅ Nenhum repositório duplicado logicamente encontrado![/green]"
            )
            return

        console.print(
            f"[bold yellow]⚠️ Encontrados {len(duplicados)} projetos clonados mais de uma vez![/bold yellow]"
        )
        for c, reps in duplicados.items():
            console.print(f"\n[cyan]{c}[/cyan]")
            for r in reps:
                console.print(f"  - {r.path} [dim]({r.remote_url})[/dim]")

        if plan:
            console.print(
                "\n[dim]Modo --plan ativado. Nenhuma deleção será feita.[/dim]"
            )
            return

        # Opcional (Futuro): Perguntar qual clone manter e deletar os outros usando python shutil/rmtree


@catalog_app.command("open")
def open_repo(query: str):
    """Busca rápida por nome ou host/owner e abre no VS Code ou gerenciador."""
    init_db()
    with Session(engine) as session:
        # Busca case-insensitive super simples
        repos = session.exec(select(Repo)).all()
        matches = [
            r
            for r in repos
            if query.lower() in r.path.lower()
            or (r.canonical_name and query.lower() in r.canonical_name.lower())
        ]

        if not matches:
            console.print(
                f"[red]❌ Nenhum repositório encontrado para '{query}'.[/red]"
            )
            return

        if len(matches) == 1:
            target = matches[0].path
        else:
            console.print(
                f"[yellow]Foram encontrados {len(matches)} resultados:[/yellow]"
            )
            for i, r in enumerate(matches):
                console.print(f"[{i}] {r.canonical_name or r.name} ({r.path})")

            escolha = typer.prompt("Qual você quer abrir?", type=int)
            if 0 <= escolha < len(matches):
                target = matches[escolha].path
            else:
                console.print("[red]Opção inválida.[/red]")
                return

        console.print(f"[green]Abrindo {target}...[/green]")
        # Suporta VS Code se estiver no path, senao fallback
        if platform.system() == "Windows":
            os.system(f'code "{target}"')
        elif platform.system() == "Darwin":  # macOS
            os.system(f'code "{target}" || open "{target}"')
        else:
            os.system(f'code "{target}" || xdg-open "{target}"')
