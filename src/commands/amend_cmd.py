import git
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from src.core.git_ops import GitService

console = Console()

def handle_ai_amend(cli):
    if not cli.repos:
        return
        
    repo_idx = IntPrompt.ask("Digite o ID do repositório para usar a IA")
    if 0 <= repo_idx < len(cli.repos):
        repo_path = cli.repos[repo_idx]
        details = GitService.get_repo_details(repo_path)
        
        if not details.get('commits'):
            console.print("[red]Repositório vazio ou sem commits.[/red]")
            return
            
        commits = details['commits']
        page = 0
        per_page = 15
        
        mode = "0"
        while True:
            console.print(f"\n[cyan]Repositório:[/] {repo_path}")
            commits_table = Table(title=f"Histórico (Página {page+1} de {(len(commits)-1)//per_page + 1})", show_header=True, header_style="bold blue")
            commits_table.add_column("Índice", style="dim", width=4)
            commits_table.add_column("Hash", style="yellow")
            commits_table.add_column("Mensagem Atual")
            
            start = page * per_page
            end = start + per_page
            
            for i in range(start, min(end, len(commits))):
                c = commits[i]
                commits_table.add_row(str(i), c['hash'], c['message'][:60] + "...")
            console.print(commits_table)
            
            console.print("\n[bold yellow]Ações de Revisão e Paginação:[/bold yellow]")
            console.print("[1] 🎯 Revisar um único commit específico")
            console.print("[2] 🔄 Revisão Sequencial em Lote (O Mais Recente -> O Mais Antigo)")
            
            valid_choices = ["0", "1", "2"]
            if end < len(commits):
                console.print("[3] 📄 Ver próximos commits (Mais Antigos)")
                valid_choices.append("3")
            if page > 0:
                console.print("[4] 📄 Ver commits anteriores (Mais Recentes)")
                valid_choices.append("4")
            console.print("[0] 🔙 Cancelar / Voltar")
            
            mode = Prompt.ask("Escolha a ação", choices=valid_choices, default="1")
            
            if mode == "0":
                return
            elif mode == "3":
                page += 1
            elif mode == "4":
                page -= 1
            elif mode in ["1", "2"]:
                break
                
        if mode == "1":
            c_idx = IntPrompt.ask("Digite o índice do commit que deseja alterar (ex: 0 para o mais recente)")
            if 0 <= c_idx < len(commits):
                _process_single_amend(cli, repo_path, commits[c_idx])
            else:
                console.print("[red]Índice inválido.[/red]")
        else:
            n_commits = IntPrompt.ask(f"Quantos commits para trás deseja revisar sequencialmente? (Máx {len(commits)})")
            if 1 <= n_commits <= len(commits):
                for i in range(n_commits):
                    target_commit = commits[i]
                    console.print(f"\n[bold magenta]━━━━━━━━━━ Revisando Commit {i+1}/{n_commits} ━━━━━━━━━━[/bold magenta]")
                    console.print(f"[dim]Hash original: {target_commit['hash']}\nMensagem atual: {target_commit['message']}[/dim]\n")
                    
                    success = _process_single_amend(cli, repo_path, target_commit, is_batch=True)
                    if not success:
                        break
                console.print("\n[bold green]✅ Fluxo de revisão sequencial finalizado![/bold green]")
            else:
                console.print("[red]Quantidade inválida.[/red]")
            
        # Verifica se tem remote para oferecer o Push
        if "Sem remote" not in details.get('remote', "Sem remote"):
            do_push = Prompt.ask("\n[bold cyan]Deseja enviar (force push) o novo histórico para o GitHub/Remote?[/bold cyan] [S/N]", choices=["S", "N", "s", "n"], default="N")
            if do_push.upper() == 'S':
                with console.status("[bold yellow]Enviando alterações..."):
                    try:
                        repo = git.Repo(repo_path)
                        repo.git.push('--force-with-lease')
                        console.print("[bold green]✅ Push executado com sucesso![/bold green]")
                    except Exception as e:
                        console.print(f"[bold red]Erro ao fazer push:[/] {e}")

        Prompt.ask("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    else:
        console.print("[red]ID inválido![/red]")

def _process_single_amend(cli, repo_path: str, target_commit: dict, is_batch: bool = False) -> bool:
    """Processa um commit individualmente. Retorna False se o usuário cancelar o lote inteiro."""
    commit_hash = target_commit['hash']
    
    with console.status(f"[bold green]Isolando diff do commit {commit_hash}...") as status:
        diff = GitService.extract_diff_for_commit(repo_path, commit_hash)
        if not diff or diff.startswith("Não foi possível"):
            from rich.markup import escape
            console.print(f"[red]Falha ao isolar diff para o commit {commit_hash}.[/red]")
            console.print(f"[yellow]{escape(diff[:1000]) if diff else ''}[/yellow]")
            return True # Retorna True para não cancelar o lote inteiro
        
        status.update("[bold green]Enviando diff para o Ollama gerar nova mensagem...")
        suggestion = asyncio.run(cli.ollama.suggest_commit_message(diff))
        
    console.print(Panel(suggestion, title="Sugestão da IA (Ollama)", border_style="green"))
    
    # Memória de tratamento: se a mensagem atual já é exatamente a sugestão, pula automaticamente
    if target_commit['message'].strip() == suggestion.strip():
        console.print("[bold cyan]✅ Commit já passou por esse tratamento (mesma mensagem)![/bold cyan]")
        console.print("[yellow]Ação cancelada / Pulado automaticamente.[/yellow]")
        return True
        
    if is_batch:
        prompt_text = "Deseja aplicar? [S]im / [N]Pular / [E]ditar manual / [C]ancelar Lote"
        choices = ["S", "N", "E", "C", "s", "n", "e", "c"]
    else:
        prompt_text = "Deseja aplicar esta mensagem e reescrever o histórico? (S/N)"
        choices = ["S", "N", "s", "n"]
        
    confirm = Prompt.ask(prompt_text, choices=choices).upper()
    
    if confirm == 'S':
        try:
            with console.status("[bold yellow]Iniciando Rebase Interativo Automático..."):
                GitService.reword_commit(repo_path, commit_hash, suggestion)
            console.print(f"[bold green]✅ Commit atualizado com sucesso via rebase![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Erro ao fazer rebase:[/] {e}")
    elif confirm == 'E':
        edited_msg = Prompt.ask("Digite a nova mensagem do commit")
        if edited_msg.strip():
            try:
                with console.status("[bold yellow]Aplicando mensagem manual..."):
                    GitService.reword_commit(repo_path, commit_hash, edited_msg)
                console.print(f"[bold green]✅ Commit atualizado com sucesso via rebase![/bold green]")
            except Exception as e:
                console.print(f"[bold red]Erro ao fazer rebase:[/] {e}")
    elif confirm == 'C':
        console.print("[yellow]Revisão em lote cancelada pelo usuário.[/yellow]")
        return False
    else:
        console.print("[yellow]Ação cancelada / Pulado.[/yellow]")
        
    return True
