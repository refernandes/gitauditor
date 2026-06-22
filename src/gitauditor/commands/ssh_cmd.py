import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from gitauditor.core.ssh_audit import IdentityManager

console = Console()


def handle_manage_ssh(cli):
    console.print(
        Panel.fit(
            "[bold magenta]🔑 Gerenciador de Chaves e Identidades SSH[/bold magenta]"
        )
    )

    # Globals
    globals_cfg = IdentityManager.get_global_git_config()
    console.print(
        f"[b]Identidade Global Git:[/] {globals_cfg['name']} <{globals_cfg['email']}>\n"
    )

    keys = IdentityManager.list_ssh_keys()
    if not keys:
        console.print("[yellow]Nenhuma chave SSH encontrada em ~/.ssh/[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Nome do Arquivo", style="green")
        table.add_column("Caminho Completo", style="dim")
        table.add_column("Tipo de Criptografia", justify="center")

        for k in keys:
            table.add_row(k["name"], k["path"], k["type"])
        console.print(table)

        confirm = Prompt.ask(
            "\nDeseja testar a conexão SSH das suas chaves atuais com um provedor Git? (S/N)",
            choices=["S", "N", "s", "n"],
        )
        if confirm.lower() == "s":
            provider = Prompt.ask(
                "Qual provedor?",
                choices=["github.com", "gitlab.com", "bitbucket.org"],
                default="github.com",
            )
            with console.status(f"[bold blue]Testando conexão com {provider}..."):
                success = asyncio.run(
                    IdentityManager.test_provider_connection(provider)
                )
                if success:
                    console.print(
                        f"[bold green]✅ Autenticação bem-sucedida no {provider}![/bold green]"
                    )
                else:
                    console.print(
                        f"[bold red]❌ Falha na autenticação SSH com {provider}. Verifique suas chaves e o ssh-agent.[/bold red]"
                    )

    Prompt.ask("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
