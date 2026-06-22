import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gitauditor.commands.audit_cmd import normalize_git_url


def test_git_url_normalization():
    """Garante que urls ssh e https do mesmo projeto geram a mesma chave."""
    urls = [
        "git@github.com:Cisco/nethub.git",
        "https://github.com/Cisco/nethub.git",
        "https://github.com/Cisco/nethub",
        "ssh://git@github.com/Cisco/nethub.git",
    ]

    # Todas devem normalizar para o mesmo padrão
    expected = "github.com/cisco/nethub"

    for u in urls:
        assert normalize_git_url(u) == expected, f"URL {u} normalizou incorretamente!"
