import os

from gitauditor.core.policy_engine import PolicyEngine


def test_policy_engine_no_docs(tmp_git_repo):
    report = PolicyEngine.check_repository(tmp_git_repo)

    assert (
        report["score"] == 55
    )  # 100 - missing license(-10), gitignore(-10), ci(-10), codeowners(-5), contributing(-5), security(-5) = 100 - 45 = 55
    # The fixture creates `README.md`. So readme check is True.
    assert report["checks"]["readme"] is True
    assert report["score"] == 55
    assert report["checks"]["license"] is False
    assert report["checks"]["ci_cd"] is False


def test_policy_engine_with_env(tmp_git_repo):
    env_file = os.path.join(tmp_git_repo, ".env")
    with open(env_file, "w") as f:
        f.write("SECRET=123")

    os.system(f"git -C {tmp_git_repo} add .env")
    os.system(f"git -C {tmp_git_repo} commit -m 'add .env'")

    report = PolicyEngine.check_repository(tmp_git_repo)
    assert report["checks"]["env_exposed"] is True
    assert report["score"] == 5  # 55 - 50
    assert any("CRÍTICO" in c for c in report["critical"])


def test_policy_engine_perfect(tmp_git_repo):
    # Add all files to get 100
    with open(os.path.join(tmp_git_repo, "LICENSE"), "w") as f:
        f.write("MIT")
    with open(os.path.join(tmp_git_repo, ".gitignore"), "w") as f:
        f.write("node_modules/")
    os.makedirs(os.path.join(tmp_git_repo, ".github", "workflows"), exist_ok=True)
    with open(os.path.join(tmp_git_repo, "CODEOWNERS"), "w") as f:
        f.write("* @user")
    with open(os.path.join(tmp_git_repo, "CONTRIBUTING.md"), "w") as f:
        f.write("Guidelines")
    with open(os.path.join(tmp_git_repo, "SECURITY.md"), "w") as f:
        f.write("Security")

    report = PolicyEngine.check_repository(tmp_git_repo)
    assert report["score"] == 100
    assert not report["warnings"]
    assert not report["critical"]
