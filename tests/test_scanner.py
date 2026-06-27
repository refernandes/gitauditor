import pytest

from gitauditor.core.scanner import GitScanner


@pytest.mark.asyncio
async def test_scan_empty_directory(tmp_path):
    scanner = GitScanner()
    repos = await scanner.scan([str(tmp_path)])
    assert repos == []


@pytest.mark.asyncio
async def test_scan_directory_with_repos(tmp_path):
    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"
    repo1.mkdir()
    repo2.mkdir()
    (repo1 / ".git").mkdir()
    (repo2 / ".git").mkdir()

    scanner = GitScanner()
    repos = await scanner.scan([str(tmp_path)])
    assert len(repos) == 2
    assert str(repo1.resolve()) in repos
    assert str(repo2.resolve()) in repos


@pytest.mark.asyncio
async def test_scan_ignores_node_modules(tmp_path):
    nm_dir = tmp_path / "node_modules"
    nm_dir.mkdir()
    (nm_dir / ".git").mkdir()

    scanner = GitScanner()
    repos = await scanner.scan([str(tmp_path)])
    assert repos == []


@pytest.mark.asyncio
async def test_scan_finds_nested_repo_and_avoids_recursing_dot_git(tmp_path):
    repo_dir = tmp_path / "my_project"
    repo_dir.mkdir()
    git_dir = repo_dir / ".git"
    git_dir.mkdir()
    (git_dir / "objects").mkdir()

    scanner = GitScanner()
    repos = await scanner.scan([str(tmp_path)])
    assert len(repos) == 1
    assert str(repo_dir.resolve()) in repos
