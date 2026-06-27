import asyncio
import os

import git
import typer
from rich.console import Console

console = Console()


def get_git_diff(path: str, staged: bool) -> str:
    try:
        repo = git.Repo(path)
        if staged:
            # Diff between HEAD and Index (staged changes)
            diff_text = repo.git.diff("--cached")
        else:
            # Diff between Index and Working Tree (unstaged changes)
            # plus staged if we want, but let's just do unstaged here
            # Or both? Let's do HEAD vs working tree to get everything
            diff_text = repo.git.diff("HEAD")

        return diff_text
    except Exception as e:
        console.print(f"[red]Erro ao extrair diff: {e}[/red]")
        return ""


def review_command(
    path: str = typer.Option(".", help="Caminho do repositório"),
    staged: bool = typer.Option(False, "--staged", help="Analisar apenas mudanças em stage"),
):
    """
    [P3.3] Code Review Local: Analisa o diff atual buscando code smells e riscos.
    """
    path = os.path.abspath(path)
    if not os.path.exists(os.path.join(path, ".git")):
        console.print("[bold red]Este diretório não é um repositório Git.[/bold red]")
        raise typer.Exit(1)

    console.print("[cyan]Extraindo diff local...[/cyan]")
    diff_text = get_git_diff(path, staged)

    if not diff_text.strip():
        console.print("[yellow]Nenhuma mudança encontrada para analisar.[/yellow]")
        raise typer.Exit(0)

    # Truncate if too large to save LLM context
    max_diff_length = 5000
    if len(diff_text) > max_diff_length:
        console.print("[yellow]Diff muito grande. Truncando para os primeiros 5KB...[/yellow]")
        diff_text = diff_text[:max_diff_length] + "\n...[TRUNCATED]"

    console.print("[cyan]Chamando IA para review (isso pode levar alguns segundos)...[/cyan]")

    from gitauditor.core.ai_api import AIClient

    client = AIClient()

    async def run_review():
        result = await client.analyze_local_diff(diff_text)
        if not result:
            console.print("[red]✗ Falha ao obter a revisão estruturada do LLM.[/red]")
            return

        smells = result.get("smells", [])
        risks = result.get("risks", [])
        praise = result.get("praise", "")

        console.print("\n[bold magenta]=== AI Code Review ===[/bold magenta]")

        if smells:
            console.print("\n[bold yellow]⚠️ Code Smells detectados:[/bold yellow]")
            for s in smells:
                console.print(f"  - {s}")
        else:
            console.print("\n[bold green]✅ Nenhum code smell evidente detectado![/bold green]")

        if risks:
            console.print("\n[bold red]🚨 Riscos Arquiteturais/Lógicos:[/bold red]")
            for r in risks:
                console.print(f"  - {r}")
        else:
            console.print("\n[bold green]✅ Nenhum risco sério detectado![/bold green]")

        if praise:
            console.print(f"\n[bold blue]💡 Ponto Positivo:[/bold blue] {praise}")

    asyncio.run(run_review())
