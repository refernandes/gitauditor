import os
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from gitauditor.core.git_ops import GitService

console = Console()

def handle_repo_details(cli):
    if not cli.repos:
        return
        
    repo_idx = IntPrompt.ask("Digite o ID do repositório")
    if 0 <= repo_idx < len(cli.repos):
        repo_path = cli.repos[repo_idx]
        details = GitService.get_repo_details(repo_path)
        
        if 'error' in details:
            console.print(f"[bold red]Erro:[/] {details['error']}")
            return

        status_obj = cli.repo_status.get(repo_path, {"icon": "⚪", "reason": "Desconhecido"})
        if isinstance(status_obj, str):
            push_status = status_obj
            push_reason = ""
        else:
            push_status = status_obj["icon"]
            push_reason = status_obj["reason"]

        info = (
            f"[b]Repositório:[/] {details.get('name')}\n"
            f"[b]Caminho:[/] {details.get('path')}\n"
            f"[b]Remote:[/] {details.get('remote')}\n"
            f"[b]Branch:[/] {details.get('branch')}\n"
            f"[b]Status Local:[/] {'[red]Sujo[/]' if details.get('is_dirty') else '[green]Limpo[/]'}\n"
            f"[b]Status Push:[/] {push_status}\n"
            f"[b]Motivo/Log:[/] {push_reason}"
        )
        console.print(Panel(info, title="Detalhes", border_style="blue"))
        
        commits = details.get('commits', [])
        page = 0
        per_page = 15
        
        while True:
            # Commits
            commits_table = Table(title=f"Histórico (Página {page+1} de {max(1, (len(commits)-1)//per_page + 1)})", show_header=True, header_style="bold blue")
            commits_table.add_column("Hash", style="yellow")
            commits_table.add_column("Data")
            commits_table.add_column("Mensagem")
            
            start = page * per_page
            end = start + per_page
            
            for i in range(start, min(end, len(commits))):
                c = commits[i]
                commits_table.add_row(c['hash'], c['date'], c['message'][:50] + "..." if len(c['message']) > 50 else c['message'])
            
            console.print(commits_table)
            
            console.print("\n[bold yellow]Ações Gerenciais Locais:[/bold yellow]")
            console.print("[1] 📁 Mover pasta para outro local (Unificar Projetos)")
            console.print("[2] 🗑️  Deletar repositório permanentemente")
            
            valid_choices = ["0", "1", "2"]
            if end < len(commits):
                console.print("[3] 📄 Ver próximos commits (Mais Antigos)")
                valid_choices.append("3")
            if page > 0:
                console.print("[4] 📄 Ver commits anteriores (Mais Recentes)")
                valid_choices.append("4")
            console.print("[0] 🔙 Voltar ao Menu Principal")
            
            sub_choice = Prompt.ask("O que deseja fazer?", choices=valid_choices)
            
            if sub_choice == "3":
                page += 1
                continue
            elif sub_choice == "4":
                page -= 1
                continue
            elif sub_choice == "0":
                break
                
            if sub_choice == "1":
                dest_dir = Prompt.ask("Digite o caminho absoluto da pasta de destino (ex: /mnt/arquivos/Projetos)")
                if os.path.exists(dest_dir) and os.path.isdir(dest_dir):
                    final_dest = os.path.join(dest_dir, os.path.basename(repo_path))
                    confirm = Prompt.ask(f"[bold yellow]ATENÇÃO:[/] Confirmar a movimentação de [bold]{repo_path}[/] para [bold]{final_dest}[/]? (S/N)", choices=["S", "N", "s", "n"])
                    if confirm.lower() == 's':
                        try:
                            shutil.move(repo_path, final_dest)
                            cli.repos[repo_idx] = final_dest
                            cli.repo_status[final_dest] = cli.repo_status.pop(repo_path, "⚪")
                            console.print(f"[bold green]✅ Repositório movido com sucesso para {final_dest}![/bold green]")
                        except Exception as e:
                            console.print(f"[bold red]Erro ao mover repositório:[/] {e}")
                else:
                    console.print("[red]Diretório de destino inválido ou inexistente![/red]")
                    
            elif sub_choice == "2":
                confirm = Prompt.ask(f"[bold red]PERIGO:[/] Deseja MESMO deletar [bold]{repo_path}[/] do seu PC? (S/N)", choices=["S", "N", "s", "n"])
                if confirm.lower() == 's':
                    try:
                        shutil.rmtree(repo_path)
                        cli.repos.remove(repo_path)
                        if repo_path in cli.repo_status:
                            del cli.repo_status[repo_path]
                        console.print(f"[bold green]✅ Pasta {repo_path} deletada do sistema![/bold green]")
                    except Exception as e:
                        console.print(f"[bold red]Erro ao deletar:[/] {e}")
            
            if sub_choice in ["1", "2"]:
                Prompt.ask("\n[dim]Pressione Enter para continuar...[/dim]")
                break
    else:
        console.print("[red]ID inválido![/red]")
