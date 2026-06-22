import typer
import os
import subprocess
from rich.console import Console
from sqlmodel import Session, select
from gitauditor.core.catalog import engine, init_db
from gitauditor.core.models import Repo

console = Console()
worktree_app = typer.Typer(help="Gerenciador de Git Worktrees (P2)")


def find_repo_or_exit(query: str):
    init_db()
    with Session(engine) as session:
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
            raise typer.Exit(1)
        if len(matches) == 1:
            return matches[0].path

        console.print(
            "[yellow]Múltiplos encontrados, selecione um para continuar:[/yellow]"
        )
        for i, r in enumerate(matches):
            console.print(f"[{i}] {r.canonical_name or r.name} ({r.path})")

        escolha = typer.prompt("Número", type=int)
        if 0 <= escolha < len(matches):
            return matches[escolha].path
        else:
            console.print("[red]Inválido.[/red]")
            raise typer.Exit(1)


@worktree_app.command("list")
def list_worktrees(query: str):
    """Lista as worktrees ativas de um repositório."""
    path = find_repo_or_exit(query)
    console.print(f"[cyan]Worktrees de {path}:[/cyan]")
    os.system(f"git -C '{path}' worktree list")


@worktree_app.command("create")
def create_worktree(query: str, branch: str):
    """Cria uma nova worktree para uma branch, poupando espaço no disco local."""
    path = find_repo_or_exit(query)
    parent_dir = os.path.dirname(path)
    repo_name = os.path.basename(path)

    safe_branch = branch.replace("/", "-")
    dest_path = os.path.join(parent_dir, f"{repo_name}-{safe_branch}")

    if os.path.exists(dest_path):
        console.print(f"[yellow]⚠️ O diretório {dest_path} já existe![/yellow]")
        raise typer.Exit(1)

    console.print(
        f"[cyan]Criando worktree para branch '{branch}' em '{dest_path}'...[/cyan]"
    )

    res = subprocess.run(
        ["git", "worktree", "add", dest_path, branch],
        cwd=path,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        console.print("[bold green]✅ Worktree criada com sucesso![/bold green]")
        console.print(f"Você já pode abrir o código em: {dest_path}")
    else:
        console.print(f"[red]❌ Falha ao criar worktree:[/red] {res.stderr}")
