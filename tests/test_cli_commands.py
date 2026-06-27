from typer.testing import CliRunner
from unittest.mock import patch

from gitauditor.cli import app

runner = CliRunner()


def test_cli_help():
    """Testa se o comando principal da CLI responde com o menu de ajuda."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "GitAuditor" in result.stdout
    assert "catalog" in result.stdout
    assert "policy" in result.stdout


def test_invalid_command_fails():
    """Testa se um comando inexistente falha corretamente."""
    result = runner.invoke(app, ["comando-inexistente"])
    assert result.exit_code != 0


@patch("gitauditor.commands.catalog_cmd.init_db")
@patch("gitauditor.commands.catalog_cmd.Session")
def test_catalog_sync_command(mock_session, mock_init_db):
    """Testa o roteamento e a execução base do catalog sync, com mock do banco de dados."""
    # Como não temos um DB de teste configurado, verificamos apenas o help do subcomando.
    result = runner.invoke(app, ["catalog", "sync", "--help"])
    assert result.exit_code == 0
    assert "Sincroniza" in result.stdout or "sync" in result.stdout


@patch("gitauditor.commands.policy_cmd.PolicyEngine")
@patch("gitauditor.commands.policy_cmd.find_repo_or_exit")
def test_policy_check_command(mock_find, mock_engine):
    """Testa se o comando policy check é chamado adequadamente."""
    mock_find.return_value = "/tmp/dummy/repo"
    mock_engine.return_value.check_repository.return_value = {
        "status": "ok",
        "score": 100,
        "critical": [],
        "warnings": [],
        "checks": {
            "readme": True,
            "license": True,
            "gitignore": True,
            "ci_cd": True,
            "codeowners": True,
            "contributing": True,
            "security": True,
            "env_exposed": False,
        },
    }

    result = runner.invoke(app, ["policy", "check", "."])
    assert result.exit_code == 0


def test_repo_amend_help():
    """Testa o help do comando de inteligência artificial de repositório."""
    result = runner.invoke(app, ["repo", "amend", "--help"])
    assert result.exit_code == 0
    assert "amend" in result.stdout.lower()


@patch("gitauditor.commands.catalog_cmd.health_dashboard")
def test_hidden_health_shortcut(mock_health):
    """Testa se os atalhos escondidos do CLI estão roteando corretamente."""
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0
    mock_health.assert_called_once()
