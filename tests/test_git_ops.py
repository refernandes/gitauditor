import os
import pytest
from unittest.mock import patch, MagicMock
from gitauditor.core.exceptions import ScanError
from gitauditor.core.git_ops import GitService

def test_get_commit_diff_empty_or_clean(tmp_git_repo):
    # Test diff on empty repo or HEAD where HEAD has no recent uncommitted changes
    # By default tmp_git_repo is initialized and has a README but maybe not committed
    os.system(f"git -C {tmp_git_repo} add README.md")
    os.system(f"git -C {tmp_git_repo} commit -m 'Initial commit'")
    
    diff = GitService.get_commit_diff(tmp_git_repo, "HEAD")
    assert diff is not None
    assert "Initial commit" in diff or "diff --git" in diff

def test_get_repo_details(tmp_git_repo):
    os.system(f"git -C {tmp_git_repo} add README.md")
    os.system(f"git -C {tmp_git_repo} commit -m 'Test commit log'")
    
    details = GitService.get_repo_details(tmp_git_repo)
    assert details["name"] == "test_repo"
    assert details["is_dirty"] is False
    assert len(details["commits"]) >= 1
    assert details["commits"][0]["message"] == "Test commit log"
    
    # Test remote url mapping
    assert "remote" in details

def test_sanitize_hash():
    assert GitService._sanitize_hash("abc123def456") == "abc123def456"
    assert GitService._sanitize_hash("invalid#hash") == "invalidhash"
    with pytest.raises(ScanError, match="Invalid commit hash format"):
        GitService._sanitize_hash("git--show")

def test_amend_commit_message(tmp_git_repo):
    os.system(f"git -C {tmp_git_repo} add README.md")
    os.system(f"git -C {tmp_git_repo} commit -m 'Old Message'")
    
    GitService.amend_commit_message(tmp_git_repo, "New Message")
    details = GitService.get_repo_details(tmp_git_repo)
    assert details["commits"][0]["message"] == "New Message"

def test_rebase_flags(tmp_git_repo):
    # Just basic coverage of the shell calls, assuming no active rebase
    assert GitService.is_rebasing(tmp_git_repo) is False
    # Calling abort or continue when not rebasing shouldn't crash
    GitService.abort_rebase(tmp_git_repo)
    GitService.continue_rebase(tmp_git_repo)
    
@patch("subprocess.run")
def test_start_interactive_rebase(mock_run, tmp_git_repo):
    GitService.start_interactive_rebase(tmp_git_repo, 5)
    mock_run.assert_called()

def test_extract_diff_for_commit(tmp_git_repo):
    os.system(f"git -C {tmp_git_repo} add README.md")
    os.system(f"git -C {tmp_git_repo} commit -m 'Commit 1'")
    with open(f"{tmp_git_repo}/README.md", "a") as f:
        f.write("Line 2\n")
    os.system(f"git -C {tmp_git_repo} commit -am 'Commit 2'")
    
    diff = GitService.extract_diff_for_commit(tmp_git_repo, "HEAD")
    assert "Line 2" in diff
    
    # Invalid commit
    assert "Não foi possível obter o diff" in GitService.extract_diff_for_commit(tmp_git_repo, "invalidhash")

def test_find_open_branches(tmp_git_repo):
    os.system(f"git -C {tmp_git_repo} add README.md")
    os.system(f"git -C {tmp_git_repo} commit -m 'C1'")
    os.system(f"git -C {tmp_git_repo} branch test-branch")
    
    branches = GitService.find_open_branches(tmp_git_repo)
    assert "test-branch" in branches
    assert "main" in branches or "master" in branches
    
    # Invalid path
    assert GitService.find_open_branches("/non/existent/path") == []

def test_get_latest_commit_info(tmp_git_repo):
    os.system(f"git -C {tmp_git_repo} add README.md")
    os.system(f"git -C {tmp_git_repo} commit -m 'Commit Msg 123'")
    
    info = GitService.get_latest_commit_info(tmp_git_repo)
    assert info["message"] == "Commit Msg 123"
    assert info["date"] != "1970-01-01 00:00"

    # Invalid path
    bad_info = GitService.get_latest_commit_info("/non/existent/path")
    assert bad_info["message"] == "N/A"

@patch("subprocess.run")
def test_reword_commit_success(mock_run, tmp_git_repo):
    mock_run.return_value = MagicMock(returncode=0)
    # Using patch for 'git.Repo' and other internals to avoid actually rewriting real commits in testing if it's too complex
    with patch("git.Repo") as mock_repo:
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        # Fake commit parents
        mock_repo_instance.commit.return_value = MagicMock(parents=[MagicMock()])
        
        backup_branch = GitService.reword_commit(tmp_git_repo, "abc1234", "New Message")
        assert backup_branch.startswith("gitauditor-backup-")
        mock_run.assert_called()

def test_rollback_amend_success(tmp_git_repo):
    os.system(f"git -C {tmp_git_repo} add README.md")
    os.system(f"git -C {tmp_git_repo} commit -m 'Initial'")
    os.system(f"git -C {tmp_git_repo} branch backup-branch")
    
    assert GitService.rollback_amend(tmp_git_repo, "backup-branch") is True
    
    with pytest.raises(ScanError):
        GitService.rollback_amend(tmp_git_repo, "non-existent-branch")
