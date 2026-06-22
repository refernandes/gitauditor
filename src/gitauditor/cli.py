import os
import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from gitauditor.core.scanner import GitScanner
from gitauditor.core.ollama_api import OllamaClient

from gitauditor.commands.repo_cmd import handle_repo_details
from gitauditor.commands.amend_cmd import handle_ai_amend
from gitauditor.commands.ssh_cmd import handle_manage_ssh
from gitauditor.commands.audit_cmd import handle_audit_duplicates
from gitauditor.commands.catalog_cmd import catalog_app

console = Console()


class GitAuditorCLI:
    def __init__(self):
        self.scanner = GitScanner()
        self.ollama = OllamaClient()
        self.repos = []
        self.repo_status = {}
        self.current_filter = "Todos"

    def run(self):
        console.clear()
        console.print(
            Panel.fit(
                "[bold cyan]🚀 Git Auditor & IA Manager[/bold cyan]",
                border_style="cyan",
            )
        )

        # Step 1: Load Catalog
        self._load_catalog()

        # Step 2: Main Loop
        while True:
            self._show_repo_table()

            console.print("\n[bold yellow]Menu Principal:[/bold yellow]")
            console.print("[1] 🔍 Ver Detalhes de um Repositório")
            console.print("[2] 🤖 IA Amend (Reescrever histórico guiado por IA)")
            console.print("[3] 🔑 Gerenciar Chaves e Identidades SSH")
            console.print("[4] 🧹 Auditoria de Repositórios (Duplicados e Branches)")
            console.print(
                f"[6] 🏷️  Filtrar Tabela (Atual: [bold green]{self.current_filter}[/bold green])"
            )
            console.print("[0] 🚪 Sair")

            choice = Prompt.ask(
                "Escolha uma opção", choices=["0", "1", "2", "3", "4", "5", "6"]
            )

            if choice == "0":
                console.print("[bold green]Até logo![/bold green] 👋")
                break
            elif choice == "1":
                handle_repo_details(self)
            elif choice == "2":
                handle_ai_amend(self)
            elif choice == "3":
                handle_manage_ssh(self)
            elif choice == "4":
                handle_audit_duplicates(self)
            elif choice == "5":
                from gitauditor.commands.catalog_cmd import sync_catalog

                sync_catalog()
                self._load_catalog()
            elif choice == "6":
                self._action_filter_table()

    def _load_catalog(self):
        from gitauditor.core.catalog import engine, init_db
        from gitauditor.core.models import Repo
        from sqlmodel import Session, select

        init_db()
        with Session(engine) as session:
            repos_db = session.exec(select(Repo)).all()
            self.repos = [r.path for r in repos_db]

            # Map existing status from DB if any
            for r in repos_db:
                self.repo_status[r.path] = {
                    "icon": r.status if r.status != "Unknown" else "⚪",
                    "reason": "Lido do catálogo",
                }

        if not self.repos:
            console.print(
                "\n[bold yellow]⚠️ O catálogo está vazio![/bold yellow] Rode [cyan]gitauditor catalog sync[/cyan] (Opção 5) para populá-lo."
            )
        else:
            console.print(
                f"\n[dim]Carregado do catálogo local: {len(self.repos)} repositórios.[/dim]"
            )

    async def _audit_all_repos(self):
        self.repo_status.clear()

        async def check_repo(repo_path):
            status_icon = "⚪"
            reason = ""
            try:
                # 1. Verifica origin
                remote_proc = await asyncio.create_subprocess_exec(
                    "git",
                    "remote",
                    "get-url",
                    "origin",
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await remote_proc.communicate()

                if remote_proc.returncode != 0:
                    status_icon = "📁 Local"
                    reason = "Sem remote configurado"
                else:
                    # 2. Testa push dry-run explicitamente com a HEAD para evitar falso positivo de falta de tracking branch
                    push_proc = await asyncio.create_subprocess_exec(
                        "git",
                        "push",
                        "--dry-run",
                        "origin",
                        "HEAD",
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                    try:
                        stdout_data, stderr_data = await asyncio.wait_for(
                            push_proc.communicate(), timeout=5.0
                        )
                        err_str = stderr_data.decode(errors="ignore").strip()

                        if push_proc.returncode == 0 or "up-to-date" in err_str.lower():
                            status_icon = "🟢 OK"
                            reason = "Acesso SSH/Push garantido"
                        else:
                            status_icon = "🔴 Negado"
                            reason = err_str.replace("\n", " | ")
                    except asyncio.TimeoutError:
                        push_proc.kill()
                        status_icon = "⚠️ Timeout"
                        reason = "Timeout na requisição de rede"

            except Exception as e:
                status_icon = "⚠️ Erro"
                reason = str(e)

            self.repo_status[repo_path] = {"icon": status_icon, "reason": reason}

        # Dispara todas as checagens em paralelo
        tasks = [check_repo(r) for r in self.repos]
        if tasks:
            await asyncio.gather(*tasks)

    def _show_repo_table(self):
        if not self.repos:
            console.print("[yellow]Nenhum repositório para exibir.[/yellow]")
            return

        table = Table(
            title="Repositórios Encontrados",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("ID", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Caminho", style="dim")
        table.add_column("Status Push", justify="center")
        table.add_column("Motivo / Log", style="dim")

        displayed = 0
        for idx, repo_path in enumerate(self.repos):
            name = os.path.basename(repo_path)

            status_obj = self.repo_status.get(repo_path, {"icon": "⚪", "reason": ""})
            if isinstance(status_obj, str):  # Backward compatibility just in case
                icon = status_obj
                reason = ""
            else:
                icon = status_obj["icon"]
                reason = status_obj["reason"]

            # Filter logic
            if self.current_filter == "Apenas OK" and "🟢" not in icon:
                continue
            if self.current_filter == "Apenas Negados" and "🔴" not in icon:
                continue
            if self.current_filter == "Apenas Locais" and "📁" not in icon:
                continue

            # Truncate reason
            display_reason = reason[:35] + "..." if len(reason) > 35 else reason
            table.add_row(str(idx), name, repo_path, icon, display_reason)
            displayed += 1

        if displayed > 0:
            console.print(table)
        else:
            console.print(
                f"[yellow]Nenhum repositório corresponde ao filtro: {self.current_filter}[/yellow]"
            )

    def _action_filter_table(self):
        console.print("\n[bold cyan]Opções de Filtro:[/bold cyan]")
        console.print("[1] Todos")
        console.print("[2] Apenas OK 🟢")
        console.print("[3] Apenas Negados 🔴")
        console.print("[4] Apenas Locais 📁")

        choice = Prompt.ask(
            "Escolha o filtro", choices=["1", "2", "3", "4"], default="1"
        )
        if choice == "1":
            self.current_filter = "Todos"
        elif choice == "2":
            self.current_filter = "Apenas OK"
        elif choice == "3":
            self.current_filter = "Apenas Negados"
        elif choice == "4":
            self.current_filter = "Apenas Locais"


app = typer.Typer(help="GitAuditor CLI - IA Manager", invoke_without_command=True)
app.add_typer(
    catalog_app, name="catalog", help="Gerenciamento Inteligente do Catálogo (V3)"
)
cli_state = GitAuditorCLI()


@app.callback()
def main_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        cli_state.run()


@app.command()
def scan():
    """Realiza a varredura e exibe a tabela de repositórios."""
    cli_state._load_catalog()
    cli_state._show_repo_table()


@app.command()
def amend():
    """IA Amend (Reescrever histórico guiado por IA)."""
    cli_state._load_catalog()
    cli_state._show_repo_table()
    handle_ai_amend(cli_state)


@app.command()
def audit():
    """Auditoria de Repositórios (Duplicados e Branches)."""
    cli_state._load_catalog()
    handle_audit_duplicates(cli_state)


@app.command()
def ssh():
    """Gerenciar Chaves e Identidades SSH."""
    handle_manage_ssh(cli_state)


@app.command()
def details():
    """Ver Detalhes de um Repositório."""
    cli_state._load_catalog()
    cli_state._show_repo_table()
    handle_repo_details(cli_state)


if __name__ == "__main__":
    app()
