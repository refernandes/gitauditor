import os
import shutil
from collections import defaultdict

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from gitauditor.core.git_ops import GitService

console = Console()


def normalize_git_url(url: str) -> str:
    """Normaliza uma URL do Git removendo protocolos e sufixos para fácil comparação."""
    if not url or url == "Sem remote 'origin'":
        return url

    url = url.lower().strip()

    # Remove prefixos
    for prefix in ["https://", "http://", "ssh://", "git@"]:
        if url.startswith(prefix):
            url = url[len(prefix) :]

    # Remove sufixo
    if url.endswith(".git"):
        url = url[:-4]

    # Converte : em / (ex: github.com:user/repo -> github.com/user/repo)
    url = url.replace(":", "/")
    return url


def handle_audit_duplicates(cli):
    if not cli.repos:
        console.print("[yellow]Nenhum repositório para auditar.[/yellow]")
        return

    console.print(
        Panel.fit("[bold magenta]🧹 Auditoria de Duplicados e Branches[/bold magenta]")
    )

    url_map = defaultdict(list)
    for path in cli.repos:
        details = GitService.get_repo_details(path)
        remote = details.get("remote", "")
        if remote and remote != "Sem remote 'origin'":
            norm_url = normalize_git_url(remote)
            url_map[norm_url].append(path)

    duplicate_sets = []
    for url, paths in url_map.items():
        if len(paths) > 1:
            duplicate_sets.append((url, paths))

    if not duplicate_sets:
        console.print(
            "[green]Nenhum repositório duplicado encontrado apontando para o mesmo origin![/green]"
        )
        Prompt.ask("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        return

    for set_idx, (url, paths) in enumerate(duplicate_sets):
        console.print(
            f"\n[bold red]⚠️ Set [{set_idx}] - Duplicados para o remote:[/] {url}"
        )

        dup_table = Table(show_header=True, header_style="bold yellow")
        dup_table.add_column("Path ID", style="dim", width=7)
        dup_table.add_column("Caminho Local")
        dup_table.add_column("Branches Abertas")
        dup_table.add_column("Último Commit (Data e Mensagem)", style="cyan")

        for p_idx, p in enumerate(paths):
            info = GitService.get_latest_commit_info(p)
            branches = GitService.find_open_branches(p)
            b_str = ", ".join(branches) if branches else "Nenhuma"
            commit_str = f"{info['date']} - {info['message']}"
            dup_table.add_row(str(p_idx), p, b_str, commit_str)

        console.print(dup_table)

    console.print("\n[bold yellow]Ações de Gerenciamento de Duplicados:[/bold yellow]")
    console.print("[1] 🗑️  Deletar cópia obsoleta permanentemente")
    console.print("[2] 📁 Mover cópia para diretório diferente")
    console.print("[0] 🔙 Voltar ao Menu Principal")

    choice = Prompt.ask("O que deseja fazer?", choices=["0", "1", "2"])
    if choice == "0":
        return

    set_idx = IntPrompt.ask("Qual [Set ID] de duplicados deseja gerenciar?")
    if 0 <= set_idx < len(duplicate_sets):
        url, paths = duplicate_sets[set_idx]
        p_idx = IntPrompt.ask("Qual [Path ID] da cópia que deseja modificar?")
        if 0 <= p_idx < len(paths):
            target_path = paths[p_idx]

            if choice == "1":
                confirm = Prompt.ask(
                    f"[bold red]ATENÇÃO:[/] Deseja MESMO deletar PERMANENTEMENTE a pasta [bold]{target_path}[/]? (S/N)",
                    choices=["S", "N", "s", "n"],
                )
                if confirm.lower() == "s":
                    try:
                        shutil.rmtree(target_path)
                        cli.repos.remove(target_path)
                        if target_path in cli.repo_status:
                            del cli.repo_status[target_path]
                        console.print(
                            f"[bold green]✅ Cópia duplicada {target_path} deletada com sucesso![/bold green]"
                        )
                    except Exception as e:
                        console.print(f"[bold red]Erro ao deletar:[/] {e}")

            elif choice == "2":
                dest_dir = Prompt.ask(
                    "Digite o caminho do diretório destino (ex: /mnt/arquivos/ProjetosUnificados)"
                )
                if os.path.exists(dest_dir) and os.path.isdir(dest_dir):
                    final_dest = os.path.join(dest_dir, os.path.basename(target_path))
                    confirm = Prompt.ask(
                        f"[bold yellow]ATENÇÃO:[/] Mover de [bold]{target_path}[/] para [bold]{final_dest}[/]? (S/N)",
                        choices=["S", "N", "s", "n"],
                    )
                    if confirm.lower() == "s":
                        try:
                            shutil.move(target_path, final_dest)
                            cli.repos.remove(target_path)
                            cli.repos.append(final_dest)
                            cli.repo_status[final_dest] = cli.repo_status.pop(
                                target_path, "⚪"
                            )
                            console.print(
                                "[bold green]✅ Repositório unificado e movido com sucesso![/bold green]"
                            )
                        except Exception as e:
                            console.print(
                                f"[bold red]Erro ao mover repositório:[/] {e}"
                            )
                else:
                    console.print("[red]Diretório destino inválido![/red]")
        else:
            console.print("[red]Path ID inválido![/red]")
    else:
        console.print("[red]Set ID inválido![/red]")

    Prompt.ask("\n[dim]Pressione Enter para continuar...[/dim]")
