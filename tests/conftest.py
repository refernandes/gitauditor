import os
import pytest


@pytest.fixture
def tmp_git_repo(tmp_path):
    """Cria um repositório Git real temporário para testes."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Initialize git repo with config
    os.system(f"git init {repo_dir}")
    os.system(f"git -C {repo_dir} config user.email 'test@example.com'")
    os.system(f"git -C {repo_dir} config user.name 'Test User'")
    
    (repo_dir / "README.md").write_text("# Test")
    
    return str(repo_dir)


@pytest.fixture
def mock_ai_client(mocker):
    return mocker.patch("gitauditor.core.ai_api.AIClient")
