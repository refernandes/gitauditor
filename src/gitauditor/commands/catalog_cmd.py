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


@catalog_app.command("summarize")
def summarize_catalog(
    path: str = typer.Option(None, help="Filtrar por nome do repositório"),
    force: bool = typer.Option(
        False, "--force", help="Ignorar o cache de hash e forçar nova análise"
    ),
):
    """
    [P3] Analisa a árvore de pastas e manifestos para gerar metadados semânticos via IA.
    """
    import asyncio
    from gitauditor.core.catalog import engine, init_db
    from gitauditor.core.models import Repo
    from sqlmodel import Session, select
    from gitauditor.core.semantic import extract_repo_context
    from gitauditor.core.ollama_api import OllamaClient
    from datetime import datetime

    init_db()
    client = OllamaClient()

    with Session(engine) as session:
        query = select(Repo)
        if path:
            query = query.where(Repo.path.contains(path))

        repos = session.exec(query).all()
        if not repos:
            console.print("[red]Nenhum repositório encontrado.[/red]")
            raise typer.Exit(1)

        console.print(
            f"[bold cyan]Processando análise semântica em {len(repos)} repositórios...[/bold cyan]"
        )

        async def analyze_all():
            for repo in repos:
                console.print(f"\n[bold yellow]Analisando:[/bold yellow] {repo.name}")
                context = extract_repo_context(repo.path)
                current_hash = context["source_hash"]

                if current_hash == "none":
                    console.print("[dim]Pasta não existe mais. Pulando.[/dim]")
                    continue

                if not force and repo.ai_source_hash == current_hash:
                    console.print("[green]✓ Cache válido. Hash não mudou.[/green]")
                    continue

                console.print(f"[dim]Construindo contexto e chamando Ollama...[/dim]")

                ctx_str = f"TREE:\n{context['tree']}\n\nMANIFESTS:\n{context['manifests']}\n\nREADME:\n{context['readme']}"
                result = await client.analyze_repo_semantics(ctx_str)

                if result:
                    repo.ai_summary = result.get("summary")
                    repo.ai_stack = result.get("stack")
                    repo.ai_tags = (
                        ",".join(result.get("tags", []))
                        if isinstance(result.get("tags"), list)
                        else result.get("tags", "")
                    )
                    repo.ai_risk = result.get("risk")

                    # Governance
                    repo.ai_model = client.model
                    repo.ai_source_hash = current_hash
                    repo.ai_updated_at = datetime.utcnow()

                    session.add(repo)
                    session.commit()

                    console.print(
                        f"[green]✓ Atualizado![/green] Stack: [cyan]{repo.ai_stack}[/cyan]"
                    )
                    console.print(f"  [dim]Tags: {repo.ai_tags}[/dim]")
                    console.print(f"  [dim]Resumo: {repo.ai_summary}[/dim]")
                else:
                    console.print(
                        "[red]✗ Falha ao processar a resposta estruturada do LLM.[/red]"
                    )

        asyncio.run(analyze_all())


@catalog_app.command("tag-auto")
def tag_auto_catalog(
    path: str = typer.Option(None, help="Filtrar por nome do repositório"),
    no_ai: bool = typer.Option(
        False, "--no-ai", help="Usar apenas heurística bruta (sem Ollama)"
    ),
):
    """
    [P3.2] Híbrido: Gera e aplica tags automaticamente (Heurística determinística + LLM).
    """
    import asyncio
    from gitauditor.core.catalog import engine, init_db
    from gitauditor.core.models import Repo
    from sqlmodel import Session, select
    from gitauditor.core.heuristics import generate_heuristic_tags
    from gitauditor.core.semantic import extract_repo_context
    from gitauditor.core.ollama_api import OllamaClient

    init_db()
    client = OllamaClient()

    with Session(engine) as session:
        query = select(Repo)
        if path:
            query = query.where(Repo.path.contains(path))

        repos = session.exec(query).all()
        if not repos:
            console.print("[red]Nenhum repositório encontrado.[/red]")
            raise typer.Exit(1)

        console.print(
            f"[bold cyan]Processando auto-tagging em {len(repos)} repositórios...[/bold cyan]"
        )

        async def tag_all():
            for repo in repos:
                console.print(f"\n[bold yellow]Analisando:[/bold yellow] {repo.name}")

                # 1. Fallback Determinístico (Heuristics)
                h_tags = generate_heuristic_tags(repo.path)
                console.print(f"  [dim]Heurística base detectada:[/dim] {h_tags}")

                final_tags = h_tags

                # 2. LLM Enrichment (se permitido)
                if not no_ai:
                    context = extract_repo_context(repo.path)
                    if context["source_hash"] != "none":
                        ctx_str = f"TREE:\n{context['tree']}\nMANIFESTS:\n{context['manifests']}\nREADME:\n{context['readme']}"
                        refined = await client.refine_repo_tags(ctx_str, h_tags)
                        if refined:
                            final_tags = refined

                # Update DB
                tag_str = ",".join(final_tags)
                repo.tags = tag_str
                session.add(repo)
                session.commit()

                console.print(
                    f"  [green]✓ Tags aplicadas:[/green] [bold cyan]{tag_str}[/bold cyan]"
                )

        asyncio.run(tag_all())
