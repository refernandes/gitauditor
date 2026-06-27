from rich.console import Console
from rich.prompt import Prompt

from gitauditor.core.config import ConfigManager

console = Console()


def config_command():
    """
    Configurações de Inteligência Artificial (Provedor, Modelo e API Key).
    """
    config = ConfigManager.load_config()
    ai_config = config.get("ai", {})

    console.print(
        "\n[bold magenta]=== Configuração de IA do GitAuditor ===[/bold magenta]"
    )
    console.print(
        "[dim]Escolha qual provedor de Inteligência Artificial você quer usar.[/dim]\n"
    )

    provider_choices = ["ollama", "openai", "openrouter", "azure"]
    current_provider = ai_config.get("provider", "ollama")

    console.print("Provedores disponíveis:")
    console.print("  [1] Ollama (Local, Gratuito, Seguro)")
    console.print("  [2] OpenAI (Nuvem, Pago, Muito inteligente)")
    console.print("  [3] OpenRouter (Nuvem, Multi-modelos, Pago/Gratuito)")
    console.print("  [4] Azure AI (Nuvem Corporativa Microsoft)")

    choice = Prompt.ask(
        "Selecione o provedor",
        choices=["1", "2", "3", "4"],
        default=str(provider_choices.index(current_provider) + 1)
        if current_provider in provider_choices
        else "1",
    )

    selected_provider = provider_choices[int(choice) - 1]
    ai_config["provider"] = selected_provider

    # Defaults and prompts based on provider
    if selected_provider == "ollama":
        current_model = ai_config.get("model", "llama3")
        ai_config["model"] = Prompt.ask("Qual modelo do Ollama?", default=current_model)

        current_url = ai_config.get("base_url", "http://localhost:11434")
        ai_config["base_url"] = Prompt.ask("URL base do Ollama", default=current_url)

        ai_config["api_key"] = ""

    elif selected_provider == "openai":
        current_model = ai_config.get("model", "gpt-4o-mini")
        ai_config["model"] = Prompt.ask("Qual modelo da OpenAI?", default=current_model)

        current_key = ai_config.get("api_key", "")
        # mask key if it exists
        mask = "*" * 10 + current_key[-4:] if len(current_key) > 4 else ""
        new_key = Prompt.ask(f"Sua API Key [dim](Atual: {mask})[/dim]", password=True)
        if new_key:
            ai_config["api_key"] = new_key

        ai_config["base_url"] = "https://api.openai.com/v1"

    elif selected_provider == "openrouter":
        current_model = ai_config.get("model", "meta-llama/llama-3-8b-instruct")
        ai_config["model"] = Prompt.ask(
            "Qual modelo do OpenRouter? (ex: google/gemini-flash-1.5)",
            default=current_model,
        )

        current_key = ai_config.get("api_key", "")
        mask = "*" * 10 + current_key[-4:] if len(current_key) > 4 else ""
        new_key = Prompt.ask(
            f"Sua OpenRouter API Key [dim](Atual: {mask})[/dim]", password=True
        )
        if new_key:
            ai_config["api_key"] = new_key

        ai_config["base_url"] = "https://openrouter.ai/api/v1"

    elif selected_provider == "azure":
        current_model = ai_config.get("model", "gpt-4o")
        ai_config["model"] = Prompt.ask("Qual deployment name (modelo)?", default=current_model)

        current_url = ai_config.get("base_url", "https://renansousa-2956-resource.services.ai.azure.com/openai/v1")
        ai_config["base_url"] = Prompt.ask("URL base do Azure AI", default=current_url)

        use_default_cred = Prompt.ask("Usar Entra ID (DefaultAzureCredential)? [S/n]", default="s")
        if use_default_cred.lower() == 's':
            ai_config["api_key"] = "azure_default_credential"
        else:
            current_key = ai_config.get("api_key", "")
            mask = "*" * 10 + current_key[-4:] if len(current_key) > 4 else ""
            new_key = Prompt.ask(f"Sua API Key do Azure [dim](Atual: {mask})[/dim]", password=True)
            if new_key:
                ai_config["api_key"] = new_key

    # Language Selection
    console.print("\n[dim]Configuração de Idioma / Language Settings[/dim]")
    current_lang = config.get("lang", "pt_BR")
    lang_choice = Prompt.ask(
        "Selecione o Idioma / Select Language: [1] Português (pt_BR) [2] English (en_US)",
        choices=["1", "2"],
        default="1" if current_lang == "pt_BR" else "2"
    )
    config["lang"] = "pt_BR" if lang_choice == "1" else "en_US"

    config["ai"] = ai_config
    ConfigManager.save_config(config)

    console.print("\n[bold green]✅ Configuração salva com sucesso![/bold green]")
    console.print(
        f"O GitAuditor agora usará: [bold cyan]{selected_provider.upper()}[/bold cyan] ({ai_config['model']}) em [bold]{config['lang']}[/bold]"
    )
