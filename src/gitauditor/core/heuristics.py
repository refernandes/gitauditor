import os
from typing import List


def generate_heuristic_tags(repo_path: str) -> List[str]:
    """
    P3.2: Deterministic auto-tagging based on path and file contents.
    Provides a solid baseline before LLM enrichment.
    """
    tags = set()

    # 1. Path-based heuristics
    lower_path = repo_path.lower()
    if (
        "/lab" in lower_path
        or "/poc" in lower_path
        or "test" in os.path.basename(repo_path).lower()
    ):
        tags.add("lab")
    if "/work" in lower_path or "/client" in lower_path or "/company" in lower_path:
        tags.add("work")
    if "/study" in lower_path or "/curso" in lower_path or "/learn" in lower_path:
        tags.add("study")
    if "/archive" in lower_path or "/old" in lower_path:
        tags.add("archive")

    # 2. Infra / Ops
    if (
        os.path.exists(os.path.join(repo_path, "docker-compose.yml"))
        or os.path.exists(os.path.join(repo_path, "Dockerfile"))
        or os.path.exists(os.path.join(repo_path, "k8s"))
    ):
        tags.add("infra")

    if os.path.exists(os.path.join(repo_path, "terraform")) or os.path.exists(
        os.path.join(repo_path, "main.tf")
    ):
        tags.add("infra")

    # 3. Node.js Ecosystem
    pkg_json = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_json):
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                content = f.read().lower()
                if (
                    "react" in content
                    or "next" in content
                    or "vue" in content
                    or "svelte" in content
                ):
                    tags.add("frontend")
                if "express" in content or "nest" in content or "fastify" in content:
                    tags.add("api")
                if "react-native" in content or "expo" in content:
                    tags.add("mobile")
        except Exception:
            tags.add("javascript")

    # 4. Python Ecosystem
    req_txt = os.path.join(repo_path, "requirements.txt")
    py_toml = os.path.join(repo_path, "pyproject.toml")

    if os.path.exists(req_txt) or os.path.exists(py_toml):
        tags.add("python")
        try:
            content = ""
            if os.path.exists(req_txt):
                with open(req_txt, "r", encoding="utf-8") as f:
                    content += f.read().lower()
            if os.path.exists(py_toml):
                with open(py_toml, "r", encoding="utf-8") as f:
                    content += f.read().lower()

            if "fastapi" in content or "flask" in content or "django" in content:
                tags.add("api")
            if "pandas" in content or "scikit" in content or "numpy" in content:
                tags.add("data-science")
            if "typer" in content or "click" in content or "rich" in content:
                tags.add("cli")
        except Exception:
            pass

    # 5. Go / Rust
    if os.path.exists(os.path.join(repo_path, "go.mod")):
        tags.add("go")
    if os.path.exists(os.path.join(repo_path, "Cargo.toml")):
        tags.add("rust")

    return list(tags)
