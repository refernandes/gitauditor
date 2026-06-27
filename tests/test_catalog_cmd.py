import pytest
from unittest.mock import patch, AsyncMock
from typer.testing import CliRunner
from sqlmodel import create_engine, SQLModel, Session
from gitauditor.commands.catalog_cmd import catalog_app
from gitauditor.core.models import Repo

runner = CliRunner()


@pytest.fixture
def mock_db_engine():
    """Mock the DB engine to use an in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    # We patch the engine in both catalog_cmd and catalog modules where it's used
    with patch("gitauditor.commands.catalog_cmd.engine", engine), \
         patch("gitauditor.core.catalog.engine", engine):
        yield engine


def test_sync_catalog(mock_db_engine, tmp_git_repo):
    """Testa se sync_catalog() popula o banco corretamente com os repositórios encontrados."""
    with patch("gitauditor.commands.catalog_cmd.GitScanner") as mock_scanner_cls, \
         patch("gitauditor.commands.catalog_cmd.enrich_all", new_callable=AsyncMock) as mock_enrich:
        
        # Mock scanner to return our tmp_git_repo (it's an async function)
        mock_instance = mock_scanner_cls.return_value
        mock_instance.scan = AsyncMock(return_value=[tmp_git_repo])
        
        mock_enrich.return_value = [{
            "path": tmp_git_repo,
            "remote_url": "git@github.com/owner/test_repo.git",
            "host": "github.com",
            "owner": "owner",
            "canonical_name": "owner/test_repo",
            "status": "Synced"
        }]
        
        result = runner.invoke(catalog_app, ["sync"])
        
        assert result.exit_code == 0
        assert "Catálogo sincronizado com sucesso!" in result.stdout
        
        # Check DB
        from sqlmodel import select
        with Session(mock_db_engine) as session:
            repos = session.exec(select(Repo)).all()
            assert len(repos) == 1
            assert repos[0].path == tmp_git_repo
            assert repos[0].canonical_name == "owner/test_repo"


def test_health_dashboard_empty(mock_db_engine):
    """Testa se health_dashboard() lida bem com catálogo vazio."""
    result = runner.invoke(catalog_app, ["health"])
    assert result.exit_code == 0
    assert "O catálogo está vazio" in result.stdout


def test_health_dashboard_with_repos(mock_db_engine):
    """Testa se health_dashboard() retorna contagem correta de repos."""
    with Session(mock_db_engine) as session:
        session.add(Repo(name="repo1", path="/path/1", branch="main", status="Synced", canonical_name="a"))
        session.add(Repo(name="repo2", path="/path/2", branch="main", status="Orphan", canonical_name="b"))
        session.commit()
        
    result = runner.invoke(catalog_app, ["health"])
    assert result.exit_code == 0
    assert "Repositórios" in result.stdout
    assert "2" in result.stdout
    assert "Órfãos (Sem origin)" in result.stdout
    assert "1" in result.stdout


def test_dedupe_repos_plan(mock_db_engine):
    """Testa se dedupe_repos() em dry-run não deleta nada."""
    with Session(mock_db_engine) as session:
        session.add(Repo(name="repo1", path="/path/old", canonical_name="owner/repo1"))
        session.add(Repo(name="repo1", path="/path/new", canonical_name="owner/repo1"))
        session.commit()
        
    result = runner.invoke(catalog_app, ["dedupe", "--plan"])
    
    assert result.exit_code == 0
    assert "Modo --plan ativado. Nenhuma deleção será feita." in result.stdout
    
    # Verify nothing was deleted
    from sqlmodel import select
    with Session(mock_db_engine) as session:
        repos = session.exec(select(Repo)).all()
        assert len(repos) == 2
