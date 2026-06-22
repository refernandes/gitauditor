import os
import hashlib
from typing import Dict
from pathlib import Path
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# P3.1: Configs & Fallbacks
# ---------------------------------------------------------

MANIFEST_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "setup.py",
    "package.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "Dockerfile",
    "docker-compose.yml",
    "Makefile",
}

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".next",
}


class RepoSummarySchema(BaseModel):
    """
    Schema for Pydantic Validation of the LLM Structured Output
    """

    summary: str = Field(
        description="Short human-readable summary of the repository's purpose."
    )
    stack: str = Field(
        description="Comma separated list of main technologies detected."
    )
    tags: list[str] = Field(
        description="Suggested categories like: work, study, lab, api, infra, frontend."
    )
    risk: str = Field(
        description="Risk/Activity level: active, stale, experimental, production-ready."
    )


class RepoTagSchema(BaseModel):
    """
    P3.2: Schema for refining tags via LLM
    """

    tags: list[str] = Field(
        description="List of 2 to 5 refined tags describing the project category and architecture."
    )


# ---------------------------------------------------------
# P3.1: Hierarchical Context Extractor & Hashing
# ---------------------------------------------------------


def extract_repo_context(repo_path: str) -> Dict[str, str]:
    """
    Extracts deterministic heuristics and hierarchical content from a repository.
    Returns a dict with 'tree', 'readme', 'manifests', and the 'source_hash'.
    """
    path = Path(repo_path)
    if not path.exists() or not path.is_dir():
        return {"tree": "", "readme": "", "manifests": {}, "source_hash": "none"}

    tree_lines = []
    manifests_content = {}
    readme_content = ""

    # Walk depth 2 for tree
    for root, dirs, files in os.walk(path):
        # Filter ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        level = str(root).replace(str(path), "").count(os.sep)
        if level > 2:
            continue

        indent = " " * 4 * level
        tree_lines.append(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 4 * (level + 1)

        for f in files:
            if f.startswith("."):
                continue
            tree_lines.append(f"{subindent}{f}")

            # Extract Manifests (Only in root or depth 1)
            if level <= 1 and f in MANIFEST_FILES:
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as f_obj:
                        manifests_content[f] = f_obj.read()[
                            :2048
                        ]  # Truncate to 2KB to save tokens
                except Exception:
                    pass

            # Extract README
            if level == 0 and f.lower().startswith("readme"):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as f_obj:
                        readme_content = f_obj.read()[:3072]  # Truncate to 3KB
                except Exception:
                    pass

    tree_str = "\n".join(tree_lines)

    # Generate Invalidation Hash
    hash_input = tree_str + readme_content + str(manifests_content)
    source_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    return {
        "tree": tree_str,
        "readme": readme_content,
        "manifests": manifests_content,
        "source_hash": source_hash,
    }
