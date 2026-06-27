import os
import subprocess
import sys

import pytest

# Garante que src está no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gitauditor.core.git_ops import GitService


@pytest.fixture
def sandbox_repo_rebase(tmp_path):
    repo_dir = str(tmp_path / "repo_windows")
    os.makedirs(repo_dir)

    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)

    # Cria 3 commits
    for i in range(3):
        with open(os.path.join(repo_dir, "file.txt"), "a") as f:
            f.write(f"Line {i}\n")
        subprocess.run(["git", "add", "."], cwd=repo_dir)
        subprocess.run(["git", "commit", "-m", f"Commit {i}"], cwd=repo_dir)

    return repo_dir


def test_start_interactive_rebase_no_sed(sandbox_repo_rebase, monkeypatch):
    """Garante que start_interactive_rebase não usa 'sed' diretamente e funciona."""

    # Intercepta subprocess.run para garantir que 'sed' não seja chamado (apenas 'git')
    original_run = subprocess.run

    sed_called = False

    def mocked_run(*args, **kwargs):
        nonlocal sed_called
        cmd = args[0]
        # O comando do shell (se houver) não deve conter sed
        if isinstance(cmd, list) and cmd[0] == "sed":
            sed_called = True

        # Chama o original
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mocked_run)

    # Executa a função
    GitService.start_interactive_rebase(sandbox_repo_rebase, commits_count=2)

    assert not sed_called, "A função ainda tentou usar o comando 'sed'!"

    # Verifica se o rebase de fato pausou no estado de 'edit'
    assert GitService.is_rebasing(sandbox_repo_rebase), (
        "O repositório não entrou em estado de rebase!"
    )

    # Aborta para limpar
    GitService.abort_rebase(sandbox_repo_rebase)
