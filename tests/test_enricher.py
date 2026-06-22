from gitauditor.core.enricher import parse_remote_url


def test_parse_remote_url_ssh():
    url = "git@github.com:refernandes/gitauditor.git"
    host, owner, canonical = parse_remote_url(url)
    assert host == "github.com"
    assert owner == "refernandes"
    assert canonical == "github.com/refernandes/gitauditor"


def test_parse_remote_url_https():
    url = "https://gitlab.com/company/super-project.git"
    host, owner, canonical = parse_remote_url(url)
    assert host == "gitlab.com"
    assert owner == "company"
    assert canonical == "gitlab.com/company/super-project"


def test_parse_remote_url_https_without_git():
    url = "https://github.com/myorg/repo_without_extension"
    host, owner, canonical = parse_remote_url(url)
    assert host == "github.com"
    assert owner == "myorg"
    assert canonical == "github.com/myorg/repo_without_extension"


def test_parse_remote_url_invalid():
    url = "not_a_valid_url"
    host, owner, canonical = parse_remote_url(url)
    assert host is None
    assert owner is None
    assert canonical is None
