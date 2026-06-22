import os
import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from gitauditor.core.scanner import GitScanner
from gitauditor.core.ai_api import AIClient

from gitauditor.commands.repo_cmd import handle_repo_details
from gitauditor.commands.amend_cmd import handle_ai_amend
from gitauditor.commands.ssh_cmd import handle_manage_ssh
from gitauditor.commands.audit_cmd import handle_audit_duplicates
from gitauditor.commands.catalog_cmd import catalog_app
from gitauditor.commands.worktree_cmd import worktree_app
from gitauditor.commands.review_cmd import review_command
from gitauditor.commands.changelog_cmd import changelog_command
from gitauditor.commands.config_cmd import config_command

console = Console()


class GitAuditorCLI:
    def __init__(self):
        self.scanner = GitScanner()
        self.ai_client = AIClient()
        self.repos = []
        self.repo_status = {}
        self.current_filter = "Todos"
        self.current_page = 0
        self.page_size = 15

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
            total_filtered = self._show_repo_table()

            console.print("\n[bold yellow]Menu Principal:[/bold yellow]")
            console.print("[1] 🔍 Ver Detalhes de um Repositório")
            console.print("[2] 📂 Buscar e Abrir no Editor (Open)")
            console.print("[3] 📊 Dashboard de Saúde do Catálogo")
            console.print("[4] 🧹 Resolver Repositórios Duplicados")
            console.print("[5] 🌳 Gerenciar Git Worktrees")
            console.print("[6] 🤖 Ferramentas de Inteligência Artificial (V3)")
            console.print("[7] 🔑 Gerenciar Chaves e Identidades SSH")
            console.print("[8] 🔄 Sincronizar Catálogo Local")
            console.print(
                f"[9] 🏷️  Filtrar Tabela (Atual: [bold green]{self.current_filter}[/bold green])"
            )
            console.print("[0] 🚪 Sair")
            
            total_pages = (total_filtered + self.page_size - 1) // self.page_size if total_filtered > 0 else 1
            if total_pages > 1:
                console.print(f"[dim]Página {self.current_page + 1}/{total_pages} - Digite 'n' para próxima, 'p' para anterior[/dim]")

            choices = [str(i) for i in range(10)] + ["n", "N", "p", "P"]
            choice = Prompt.ask(
                "Escolha uma opção", choices=choices
            ).lower()

            if choice == "0":
                console.print("[bold green]Até logo![/bold green] 👋")
                break
            elif choice == "n":
                if self.current_page < total_pages - 1:
                    self.current_page += 1
                else:
                    self.current_page = 0
            elif choice == "p":
                if self.current_page > 0:
                    self.current_page -= 1
                else:
                    self.current_page = total_pages - 1
            elif choice == "1":
                handle_repo_details(self)
            elif choice == "2":
                from gitauditor.commands.catalog_cmd import open_repo

                q = Prompt.ask("Digite o nome ou parte da URL do projeto")
                open_repo(q)
                Prompt.ask("\n[dim]Pressione ENTER para continuar[/dim]")
            elif choice == "3":
                from gitauditor.commands.catalog_cmd import health_dashboard

                health_dashboard()
                Prompt.ask("\n[dim]Pressione ENTER para continuar[/dim]")
            elif choice == "4":
                from rich.prompt import Confirm
                from gitauditor.commands.catalog_cmd import dedupe_repos

                plan = Confirm.ask("Rodar em modo seguro (Dry-Run)?", default=True)
                dedupe_repos(plan=plan)
                Prompt.ask("\n[dim]Pressione ENTER para continuar[/dim]")
            elif choice == "5":
                console.print("\n[1] Listar Worktrees")
                console.print("[2] Criar Nova Worktree")
                wc = Prompt.ask("Opção", choices=["1", "2"])
                from gitauditor.commands.worktree_cmd import (
                    list_worktrees,
                    create_worktree,
                )

                q = Prompt.ask("Nome do repositório original")
                if wc == "1":
                    list_worktrees(q)
                else:
                    b = Prompt.ask("Nome da nova branch")
                    create_worktree(q, b)
                Prompt.ask("\n[dim]Pressione ENTER para continuar[/dim]")
            elif choice == "6":
                self._show_ai_menu()
            elif choice == "7":
                handle_manage_ssh(self)
            elif choice == "8":
                from gitauditor.commands.catalog_cmd import sync_catalog

                sync_catalog()
                self._load_catalog()
            elif choice == "9":
                self._action_filter_table()

    def _show_ai_menu(self):
        while True:
            console.print(
                "\n[bold magenta]🤖 Ferramentas de Inteligência Artificial:[/bold magenta]"
            )
            console.print("[1] 📝 IA Amend (Reescrever histórico guiado por IA)")
            console.print("[2] 🕵️‍♂️ IA Code Review (Analisar código não commitado)")
            console.print("[3] 📜 IA Changelog (Gerar notas de versão)")
            console.print("[4] ⚙️  IA Configuração (Mudar Provedor/Modelo)")
            console.print("[5] 🏷️  IA Auto-Tagging (Classificar repositório)")
            console.print("[6] 📚 IA Summarize (Resumir e mapear tech stack)")
            console.print("[0] 🔙 Voltar ao Menu Principal")

            ai_choice = Prompt.ask(
                "Escolha a ferramenta de IA",
                choices=["0", "1", "2", "3", "4", "5", "6"],
                default="0",
            )
            if ai_choice == "0":
                break
            elif ai_choice == "1":
                from gitauditor.commands.amend_cmd import handle_ai_amend

                handle_ai_amend(self)
            elif ai_choice == "2":
                import asyncio
                from gitauditor.commands.review_cmd import review_command

                if not self.repos:
                    console.print("[red]Catálogo vazio.[/red]")
                    continue
                repo_idx = Prompt.ask("Digite o ID do repositório")
                if repo_idx.isdigit() and 0 <= int(repo_idx) < len(self.repos):
                    repo_path = self.repos[int(repo_idx)]
                    review_command(path=repo_path)
                else:
                    console.print("[red]ID inválido![/red]")

                Prompt.ask("\n[dim]Pressione ENTER para continuar[/dim]")

            elif ai_choice == "3":
                from gitauditor.commands.changelog_cmd import changelog_command

                if not self.repos:
                    console.print("[red]Catálogo vazio.[/red]")
                    continue
                repo_idx = Prompt.ask("Digite o ID do repositório")
                if repo_idx.isdigit() and 0 <= int(repo_idx) < len(self.repos):
                    repo_path = self.repos[int(repo_idx)]
                    limit = Prompt.ask(
                        "Quantos commits analisar? (0 para todos)", default="0"
                    )
                    changelog_command(path=repo_path, limit=int(limit))
                else:
                    console.print("[red]ID inválido![/red]")

                Prompt.ask("\n[dim]Pressione ENTER para continuar[/dim]")
            elif ai_choice == "4":
                from gitauditor.commands.config_cmd import config_command

                config_command()
                Prompt.ask("\n[dim]Pressione ENTER para continuar[/dim]")
            elif ai_choice == "5":
                from gitauditor.commands.catalog_cmd import tag_auto_catalog

                if not self.repos:
                    console.print("[red]Catálogo vazio.[/red]")
                    continue
                repo_idx = Prompt.ask(
                    "Digite o ID do repositório (ou deixe em branco para rodar em todos)",
                    default="",
                )
                if repo_idx.strip() == "":
                    tag_auto_catalog(path=None)
                elif repo_idx.isdigit() and 0 <= int(repo_idx) < len(self.repos):
                    tag_auto_catalog(path=self.repos[int(repo_idx)])
                else:
                    console.print("[red]ID inválido![/red]")
                Prompt.ask("\n[dim]Pressione ENTER para continuar[/dim]")
            elif ai_choice == "6":
                from gitauditor.commands.catalog_cmd import summarize_catalog

                if not self.repos:
                    console.print("[red]Catálogo vazio.[/red]")
                    continue
                repo_idx = Prompt.ask(
                    "Digite o ID do repositório (ou deixe em branco para rodar em todos)",
                    default="",
                )
                if repo_idx.strip() == "":
                    summarize_catalog(path=None)
                elif repo_idx.isdigit() and 0 <= int(repo_idx) < len(self.repos):
                    summarize_catalog(path=self.repos[int(repo_idx)])
                else:
                    console.print("[red]ID inválido![/red]")
                Prompt.ask("\n[dim]Pressione ENTER para continuar[/dim]")

    def _load_catalog(self):
        from gitauditor.core.catalog import engine, init_db
        from gitauditor.core.models import Repo
        from sqlmodel import Session, select

        init_db()
        try:
            with Session(engine) as session:
                repos_db = session.exec(select(Repo)).all()
                self.repos = [r.path for r in repos_db]

                # Map existing status from DB if any
                for r in repos_db:
                    self.repo_status[r.path] = {
                        "icon": r.status if r.status != "Unknown" else "⚪",
                        "reason": "Lido do catálogo",
                    }
        except Exception as e:
            if "no such column" in str(e) or "no such table" in str(e):
                console.print(
                    "\n[bold red]❌ O schema do banco de dados mudou (nova atualização).[/bold red]"
                )
                console.print(
                    "[yellow]Por favor, apague o banco antigo e ressincronize:[/yellow]"
                )
                console.print(
                    "rm ~/.gitauditor/catalog.db && gitauditor catalog sync\n"
                )
                raise typer.Exit(1)
            else:
                raise

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

    def _show_repo_table(self) -> int:
        if not self.repos:
            console.print("[yellow]Nenhum repositório para exibir.[/yellow]")
            return 0

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

        # Primeiro filtramos todos
        filtered_repos = []
        for idx, repo_path in enumerate(self.repos):
            status_obj = self.repo_status.get(repo_path, {"icon": "⚪", "reason": ""})
            icon = status_obj if isinstance(status_obj, str) else status_obj["icon"]
            
            if self.current_filter == "Apenas OK" and "🟢" not in icon:
                continue
            if self.current_filter == "Apenas Negados" and "🔴" not in icon:
                continue
            if self.current_filter == "Apenas Locais" and "📁" not in icon:
                continue
            filtered_repos.append((idx, repo_path, status_obj))

        total_filtered = len(filtered_repos)
        
        # Adjust page if out of bounds
        max_page = max(0, (total_filtered - 1) // self.page_size)
        if self.current_page > max_page:
            self.current_page = max_page

        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        paged_repos = filtered_repos[start_idx:end_idx]

        for original_idx, repo_path, status_obj in paged_repos:
            name = os.path.basename(repo_path)
            if isinstance(status_obj, str):
                icon = status_obj
                reason = ""
            else:
                icon = status_obj["icon"]
                reason = status_obj["reason"]

            display_reason = reason[:35] + "..." if len(reason) > 35 else reason
            table.add_row(str(original_idx), name, repo_path, icon, display_reason)

        if total_filtered > 0:
            console.print(table)
        else:
            console.print(
                f"[yellow]Nenhum repositório corresponde ao filtro: {self.current_filter}[/yellow]"
            )
            
        return total_filtered

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
        self.current_page = 0


app = typer.Typer(help="GitAuditor CLI - IA Manager", invoke_without_command=True)
app.add_typer(
    catalog_app, name="catalog", help="Gerenciamento Inteligente do Catálogo (V3)"
)
app.add_typer(worktree_app, name="worktree", help="Gerenciador de Git Worktrees (P2)")
app.command(name="review")(review_command)
app.command(name="changelog")(changelog_command)
app.command(name="config")(config_command)
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
