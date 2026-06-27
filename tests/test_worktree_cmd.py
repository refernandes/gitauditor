import os
import subprocess
import pytest
import typer
from unittest.mock import patch, MagicMock
from sqlmodel import Session
from gitauditor.commands.worktree_cmd import (
    find_repo_or_exit,
    list_worktrees,
    create_worktree,
    clean_worktrees,
)
from gitauditor.core.models import Repo


# Mocks for DB
@pytest.fixture
def mock_db_session():
    with patch("gitauditor.commands.worktree_cmd.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session

        # Setup fake DB content
        repo1 = Repo(path="/fake/repo1", name="repo1")
        repo2 = Repo(path="/fake/repo2", name="repo2", canonical_name="my_repo2")
        mock_session.exec.return_value.all.return_value = [repo1, repo2]
        yield mock_session


def test_find_repo_or_exit_single_match(mock_db_session):
    with patch("gitauditor.commands.worktree_cmd.init_db"):
        path = find_repo_or_exit("repo1")
        assert path == "/fake/repo1"


def test_find_repo_or_exit_no_match(mock_db_session):
    with patch("gitauditor.commands.worktree_cmd.init_db"):
        with pytest.raises(typer.Exit):
            find_repo_or_exit("nonexistent")


@patch("typer.prompt")
def test_find_repo_or_exit_multiple_matches(mock_prompt, mock_db_session):
    mock_prompt.return_value = 1
    with patch("gitauditor.commands.worktree_cmd.init_db"):
        # "repo" will match both repo1 and repo2
        path = find_repo_or_exit("repo")
        assert path == "/fake/repo2"


@patch("typer.prompt")
def test_find_repo_or_exit_multiple_invalid_choice(mock_prompt, mock_db_session):
    mock_prompt.return_value = 99
    with patch("gitauditor.commands.worktree_cmd.init_db"):
        with pytest.raises(typer.Exit):
            find_repo_or_exit("repo")


@patch("os.system")
def test_list_worktrees(mock_system, mock_db_session):
    with patch("gitauditor.commands.worktree_cmd.init_db"):
        list_worktrees("repo1")
        mock_system.assert_called_once_with("git -C '/fake/repo1' worktree list")


@patch("subprocess.run")
def test_create_worktree_success(mock_run, mock_db_session):
    mock_run.return_value = MagicMock(returncode=0)
    with patch("gitauditor.commands.worktree_cmd.init_db"):
        with patch("os.path.exists", return_value=False):
            create_worktree("repo1", "feature/test")

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "add" in args
            assert "feature/test" in args
            assert "repo1-feature-test" in args[3]


@patch("subprocess.run")
def test_create_worktree_exists(mock_run, mock_db_session):
    with patch("gitauditor.commands.worktree_cmd.init_db"):
        with patch("os.path.exists", return_value=True):
            with pytest.raises(typer.Exit):
                create_worktree("repo1", "feature/test")


@patch("subprocess.run")
def test_create_worktree_failure(mock_run, mock_db_session):
    mock_run.return_value = MagicMock(returncode=1, stderr="error")
    with patch("gitauditor.commands.worktree_cmd.init_db"):
        with patch("os.path.exists", return_value=False):
            create_worktree("repo1", "feature/test")
            mock_run.assert_called_once()


# Testing clean_worktrees requires extensive subprocess mocking
@patch("subprocess.run")
def test_clean_worktrees(mock_run, mock_db_session):
    # Mocking different subprocess calls within clean_worktrees
    def side_effect(*args, **kwargs):
        cmd = args[0]
        if "prune" in cmd:
            return MagicMock(returncode=0)
        elif "list" in cmd and "--porcelain" in cmd:
            stdout = "worktree /fake/repo1-wt\nbranch refs/heads/wt\n\nworktree /fake/repo1\nbare\n"
            return MagicMock(returncode=0, stdout=stdout)
        elif "rev-parse" in cmd:
            return MagicMock(returncode=0, stdout="/fake/repo1\n")
        elif "status" in cmd:
            return MagicMock(returncode=0, stdout="")  # Clean
        elif "remove" in cmd:
            return MagicMock(returncode=0)
        return MagicMock(returncode=0)

    mock_run.side_effect = side_effect

    with patch("gitauditor.commands.worktree_cmd.init_db"):
        with patch("os.path.exists", return_value=True):
            with patch("os.walk", return_value=[("/fake/repo1-wt", [], ["file.txt"])]):
                with patch("os.path.getsize", return_value=1024):
                    clean_worktrees("repo1", force=True)

    # Should call worktree remove for the clean worktree
    remove_called = any("remove" in call.args[0] for call in mock_run.call_args_list)
    assert remove_called is True
