import typer
import os
from rich.console import Console

console = Console()
repo_app = typer.Typer(
    help=_("Operações de Repositório (Revisão, Changelog, Histórico, etc)"),
    epilog=_("""
Exemplos práticos:
  $ gitauditor repo review .                  # Analisa o diff no diretório atual
  $ gitauditor repo changelog --limit 10      # Gera notas de release para 10 commits
  $ gitauditor repo amend                     # Reescreve histórico interativamente
  $ gitauditor repo details                   # Visualiza detalhes de um projeto
""")
)

@repo_app.command("review")
def repo_review(path: str = typer.Option(".", help="Caminho do repositório"), staged: bool = typer.Option(False, "--staged")):
    """Realiza Code Review de diffs via IA."""
    from gitauditor.commands.review_cmd import review_command
    review_command(path=path, staged=staged)

@repo_app.command("changelog")
def repo_changelog(path: str = typer.Option(".", help="Caminho do repositório"), limit: int = typer.Option(0, "--limit")):
    """Gera changelog baseado no histórico de commits via IA."""
    from gitauditor.commands.changelog_cmd import changelog_command
    changelog_command(path=path, limit=limit)

@repo_app.command("amend")
def repo_amend():
    """Abre fluxo interativo para reescrever commits com IA."""
    from gitauditor.commands.amend_cmd import handle_ai_amend
    from gitauditor.cli import cli_state
    cli_state._load_catalog()
    cli_state._show_repo_table()
    handle_ai_amend(cli_state)

@repo_app.command("details")
def repo_details():
    """Visualiza detalhes e gerencia um repositório interativamente."""
    from gitauditor.commands.repo_cmd import handle_repo_details
    from gitauditor.cli import cli_state
    cli_state._load_catalog()
    cli_state._show_repo_table()
    handle_repo_details(cli_state)
