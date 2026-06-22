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
        from gitauditor.core.audit_log import AuditLogger
        AuditLogger.log("worktree_create", "SUCCESS", f"Criada branch {branch}", repo_path=dest_path)
    else:
        console.print(f"[red]❌ Falha ao criar worktree:[/red] {res.stderr}")

@worktree_app.command("clean")
def clean_worktrees(query: str, force: bool = typer.Option(False, "--force", "-f", help="Apaga sem perguntar (requer repositórios limpos)")):
    """Detecta worktrees órfãs, limpas ou sujas, e permite limpá-las com segurança."""
    import shutil
    from rich.table import Table
    from rich.prompt import Confirm
    from gitauditor.core.audit_log import AuditLogger

    path = find_repo_or_exit(query)
    
    # Prune para remover refs mortas
    subprocess.run(["git", "worktree", "prune"], cwd=path, capture_output=True)
    
    res = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=path, capture_output=True, text=True)
    if res.returncode != 0:
        console.print("[red]Erro ao listar worktrees.[/red]")
        return

    worktrees = []
    current_wt = {}
    for line in res.stdout.splitlines():
        if line.startswith("worktree "):
            if current_wt:
                worktrees.append(current_wt)
            current_wt = {"path": line.split(" ", 1)[1]}
        elif line.startswith("branch "):
            current_wt["branch"] = line.split(" ", 1)[1]
        elif line == "bare":
            current_wt["bare"] = True
    if current_wt:
        worktrees.append(current_wt)

    # Filtra a worktree principal (que costuma não ter a palavra worktree no seu .git, ou é a mesma raiz)
    main_res = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path, capture_output=True, text=True)
    main_root = main_res.stdout.strip()

    to_clean = []
    table = Table(title="Worktrees Secundárias Detectadas")
    table.add_column("Caminho", style="cyan")
    table.add_column("Branch", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Tamanho", justify="right")

    total_bytes = 0

    for wt in worktrees:
        wt_path = wt.get("path")
        if not wt_path or wt_path == main_root:
            continue

        if not os.path.exists(wt_path):
            status = "[red]Ausente (Ghost)[/red]"
            size_mb = 0
        else:
            # Pega o tamanho da pasta
            try:
                wt_size = sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, _, filenames in os.walk(wt_path) for filename in filenames)
            except Exception:
                wt_size = 0
            
            size_mb = wt_size / (1024 * 1024)
            total_bytes += wt_size
            
            # Verifica sujeira
            status_res = subprocess.run(["git", "status", "--porcelain"], cwd=wt_path, capture_output=True, text=True)
            if status_res.stdout.strip() != "":
                status = "[yellow]Suja (Uncommitted)[/yellow]"
            else:
                status = "[green]Limpa[/green]"
                to_clean.append((wt_path, wt.get("branch", "detached")))

        table.add_row(os.path.basename(wt_path), wt.get("branch", "detached").split("/")[-1], status, f"{size_mb:.1f} MB")

    console.print(table)
    
    if total_bytes == 0 and not to_clean:
        console.print("[dim]Nenhuma worktree secundária limpa para remover.[/dim]")
        return

    console.print(f"\n[bold green]Espaço recuperável estimado: {total_bytes / (1024*1024):.1f} MB[/bold green]")
    
    if not to_clean:
        console.print("[yellow]As worktrees encontradas estão SUJAS ou ausentes. Nenhuma ação automática será tomada.[/yellow]")
        return

    console.print("\nAs seguintes worktrees estão LIMPAS e prontas para remoção segura:")
    for c_path, c_branch in to_clean:
        console.print(f"- [cyan]{os.path.basename(c_path)}[/cyan]")

    if force or Confirm.ask("\nDeseja apagar essas worktrees e recuperar espaço?"):
        removed = 0
        for c_path, c_branch in to_clean:
            try:
                subprocess.run(["git", "worktree", "remove", "-f", c_path], cwd=path, check=True, capture_output=True)
                removed += 1
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Erro ao remover {c_path}:[/red] {e.stderr.decode()}")
        
        console.print(f"[bold green]Limpeza concluída! {removed} worktrees removidas.[/bold green]")
        AuditLogger.log("worktree_clean", "SUCCESS", f"Limpou {removed} worktrees em {os.path.basename(path)}", repo_path=path)
