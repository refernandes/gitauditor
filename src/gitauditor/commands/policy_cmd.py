import os
import json
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from gitauditor.core.catalog import engine, init_db
from gitauditor.core.models import Repo
from sqlmodel import Session, select
from gitauditor.core.policy_engine import PolicyEngine

console = Console()
policy_app = typer.Typer(help="Motor de Governança e Políticas (P1)")


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


@policy_app.command("check")
def check_policy(
    query: Optional[str] = typer.Argument(None, help="Nome do repositório a ser verificado"),
    output_json: bool = typer.Option(False, "--json", help="Retorna o output como JSON estruturado")
):
    """Verifica a saúde de governança de um repositório (README, CI, Secrets, etc)."""
    
    if query:
        paths_to_check = [find_repo_or_exit(query)]
    else:
        # Pega todos
        init_db()
        with Session(engine) as session:
            paths_to_check = [r.path for r in session.exec(select(Repo)).all()]

    if not paths_to_check:
        if output_json:
            print(json.dumps({"error": "Catálogo vazio"}))
        else:
            console.print("[yellow]O catálogo está vazio.[/yellow]")
        raise typer.Exit(1)

    results = {}
    for p in paths_to_check:
        try:
            report = PolicyEngine.check_repository(p)
            results[p] = report
        except Exception as e:
            results[p] = {"error": str(e)}

    # Audit logging for the command
    from gitauditor.core.audit_log import AuditLogger
    AuditLogger.log(
        "policy_check", 
        "SUCCESS", 
        f"Checou políticas para {len(paths_to_check)} repo(s).",
        details=json.dumps({"checked_count": len(paths_to_check)})
    )

    if output_json:
        # Modo integração com CI / Scripts
        print(json.dumps(results, indent=2))
        return

    # Modo Visual (Rich)
    for path, report in results.items():
        if "error" in report:
            console.print(f"[red]Erro ao checar {os.path.basename(path)}: {report['error']}[/red]")
            continue
            
        repo_name = os.path.basename(path)
        score = report["score"]
        
        color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
        
        table = Table(title=f"Governance Report: {repo_name} (Score: [{color}]{score}/100[/{color}])", show_header=True)
        table.add_column("Critério", style="cyan")
        table.add_column("Status", justify="center")

        def _format_status(passed: bool) -> str:
            return "[green]✅ Passou[/green]" if passed else "[red]❌ Falhou[/red]"

        table.add_row("README", _format_status(report["checks"]["readme"]))
        table.add_row("LICENSE", _format_status(report["checks"]["license"]))
        table.add_row("Gitignore", _format_status(report["checks"]["gitignore"]))
        table.add_row("CI/CD Pipeline", _format_status(report["checks"]["ci_cd"]))
        table.add_row("Community (CODEOWNERS/etc)", _format_status(report["checks"]["codeowners"] and report["checks"]["contributing"] and report["checks"]["security"]))
        
        env_status = "[red]❌ VAZADO[/red]" if report["checks"]["env_exposed"] else "[green]✅ Seguro[/green]"
        table.add_row("Segurança (.env commitado)", env_status)

        console.print(table)
        
        if report["critical"]:
            for crit in report["critical"]:
                console.print(f"[bold red]!! {crit} !![/bold red]")
                
        if report["warnings"]:
            console.print("[yellow]Warnings:[/yellow]")
            for w in report["warnings"]:
                console.print(f" - {w}")
                
        console.print("") # spacing
