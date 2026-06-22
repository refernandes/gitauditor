import os
import subprocess
import pytest
import sys

# Garante que src está no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gitauditor.core.git_ops import GitService


@pytest.fixture
def sandbox_repo(tmp_path):
    repo_dir = str(tmp_path / "repo")
    os.makedirs(repo_dir)

    # Inicializa repo e configura user
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True
    )

    # Cria estrutura com um merge
    # Commit A na main
    with open(os.path.join(repo_dir, "file.txt"), "w") as f:
        f.write("A")
    subprocess.run(["git", "add", "."], cwd=repo_dir)
    subprocess.run(["git", "commit", "-m", "Commit A"], cwd=repo_dir)

    # Branch feat
    subprocess.run(["git", "checkout", "-b", "feat"], cwd=repo_dir)
    with open(os.path.join(repo_dir, "file.txt"), "a") as f:
        f.write("B")
    subprocess.run(["git", "add", "."], cwd=repo_dir)
    subprocess.run(["git", "commit", "-m", "Commit B"], cwd=repo_dir)

    # Volta main, commit C
    subprocess.run(["git", "checkout", "main"], cwd=repo_dir)
    with open(os.path.join(repo_dir, "other.txt"), "w") as f:
        f.write("C")
    subprocess.run(["git", "add", "."], cwd=repo_dir)
    subprocess.run(["git", "commit", "-m", "Commit C"], cwd=repo_dir)

    # Merge feat na main -> Commit M
    subprocess.run(["git", "merge", "feat", "-m", "Merge commit M"], cwd=repo_dir)

    return repo_dir


def test_reword_preserves_merges(sandbox_repo):
    """Garante que o reword não achata commits de merge."""
    # Obter o hash do Commit A (o root commit)
    res = subprocess.run(
        ["git", "log", "--oneline"], cwd=sandbox_repo, capture_output=True, text=True
    )
    lines = res.stdout.strip().split("\n")

    commit_a_hash = lines[-1].split()[0]
    assert "Merge commit M" in res.stdout

    # Reescreve o Commit A usando o código atual
    GitService.reword_commit(sandbox_repo, commit_a_hash, "Commit A Modificado")

    # Verifica o log novamente
    res_after = subprocess.run(
        ["git", "log", "--oneline"], cwd=sandbox_repo, capture_output=True, text=True
    )

    assert "Commit A Modificado" in res_after.stdout, "O commit não foi renomeado!"
    assert "Merge commit M" in res_after.stdout, "O Rebase DESTRUIU o commit de merge!"
