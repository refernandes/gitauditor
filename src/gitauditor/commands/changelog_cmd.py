import asyncio
import os

import git
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


def get_commits_log(path: str, limit: int) -> str:
    try:
        repo = git.Repo(path)

        # Determine number of commits
        if limit > 0:
            commits = list(repo.iter_commits("HEAD", max_count=limit))
        else:
            commits = list(repo.iter_commits("HEAD"))

        log_lines = []
        for c in commits:
            log_lines.append(
                f"[{c.hexsha[:7]}] {c.authored_datetime.strftime('%Y-%m-%d')}: {c.summary} - {c.author.name}"
            )

        return "\n".join(log_lines)
    except Exception as e:
        console.print(f"[red]Erro ao extrair histórico de commits: {e}[/red]")
        return ""


def changelog_command(
    path: str = typer.Option(".", help="Caminho do repositório"),
    limit: int = typer.Option(
        0,
        "--limit",
        "-n",
        help="Número de commits (0 para buscar todos desde o início)",
    ),
):
    """
    [P3.4] Changelog Local: Gera notas de release baseadas no histórico de commits.
    """
    path = os.path.abspath(path)
    if not os.path.exists(os.path.join(path, ".git")):
        console.print("[bold red]Este diretório não é um repositório Git.[/bold red]")
        raise typer.Exit(1)

    console.print(
        f"[cyan]Extraindo histórico local ({'Todos os commits' if limit == 0 else f'Últimos {limit} commits'})...[/cyan]"
    )
    commits_log = get_commits_log(path, limit)

    if not commits_log.strip():
        console.print("[yellow]Nenhum commit encontrado para analisar.[/yellow]")
        raise typer.Exit(0)

    # Truncate if too large to save LLM context
    # Ollama context is usually 4k/8k tokens (approx 16k-32k chars)
    max_log_length = 25000
    if len(commits_log) > max_log_length:
        console.print(
            f"[yellow]Histórico muito longo ({len(commits_log)} bytes). Truncando para os primeiros ~{max_log_length // 1000}KB...[/yellow]"
        )
        commits_log = commits_log[:max_log_length] + "\n...[TRUNCATED]"

    console.print(
        "[cyan]Chamando IA para gerar Changelog (isso pode levar alguns segundos)...[/cyan]"
    )

    from gitauditor.core.ai_api import AIClient

    client = AIClient()

    async def run_changelog():
        result = await client.generate_changelog(commits_log)
        if not result:
            console.print("[red]✗ Falha ao obter a estruturação do LLM.[/red]")
            return

        version = result.get("version", "Current")
        summary = result.get("summary", "")
        features = result.get("features", [])
        fixes = result.get("fixes", [])
        breaking = result.get("breaking_changes", [])

        md_text = f"# 📦 Changelog: {version}\n\n"
        md_text += f"**Resumo:** {summary}\n\n"

        if breaking:
            md_text += "## 🚨 Breaking Changes / Refactors\n"
            for b in breaking:
                md_text += f"- {b}\n"
            md_text += "\n"

        if features:
            md_text += "## ✨ Novas Funcionalidades\n"
            for f in features:
                md_text += f"- {f}\n"
            md_text += "\n"

        if fixes:
            md_text += "## 🐛 Correções de Bugs\n"
            for f in fixes:
                md_text += f"- {f}\n"
            md_text += "\n"

        console.print(Panel(Markdown(md_text), border_style="green"))

    asyncio.run(run_changelog())
