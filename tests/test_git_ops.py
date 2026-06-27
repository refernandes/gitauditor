import os
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
