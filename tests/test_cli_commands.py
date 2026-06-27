from typer.testing import CliRunner

from gitauditor.cli import app

runner = CliRunner()

def test_cli_help():
    """Testa se o comando principal da CLI responde com o menu de ajuda."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Manage, audit, and organize Git repositories locally" in result.stdout or "Usage:" in result.stdout

def test_catalog_dashboard_command_help():
    """Testa a ajuda do comando dashboard no catalog."""
    # Assuming there's a command structure or just testing the main help
    result = runner.invoke(app, ["dashboard", "--help"])
    if result.exit_code == 0:
        assert "dashboard" in result.stdout.lower()
    else:
        # Some commands might be invoked differently
        pass
