"""
Policy engine module.

Enforces basic hygiene, community, and security governance rules on 
cataloged repositories. Calculates a health score based on standard
open-source requirements and secret leakage detection.
"""
import os
from typing import Any


class PolicyEngine:
    """
    Evaluates repository structure and contents against defined policies.
    """
    @staticmethod
    def check_repository(repo_path: str) -> dict[str, Any]:
        """
        Passive check for repository governance and health.
        
        Evaluates the presence of standard community files (README, LICENSE, etc.),
        CI/CD pipelines, and checks for critical security risks like committed .env files.
        
        Args:
            repo_path (str): The absolute path to the local git repository.
            
        Returns:
            dict[str, Any]: A report dictionary containing the final 'score', 
                            a dictionary of individual boolean 'checks', 
                            and lists for 'warnings' and 'critical' alerts.
        """

        report = {
            "score": 100,
            "checks": {},
            "warnings": [],
            "critical": []
        }

        # 1. Higiene Básica
        has_readme = any(os.path.exists(os.path.join(repo_path, f)) for f in ["README.md", "readme.md", "README.txt"])
        report["checks"]["readme"] = has_readme
        if not has_readme:
            report["score"] -= 20
            report["warnings"].append("Ausência de README.md documentando o projeto.")

        has_license = any(os.path.exists(os.path.join(repo_path, f)) for f in ["LICENSE", "LICENSE.md", "LICENSE.txt"])
        report["checks"]["license"] = has_license
        if not has_license:
            report["score"] -= 10
            report["warnings"].append("Ausência de arquivo de LICENSE explícito.")

        has_gitignore = os.path.exists(os.path.join(repo_path, ".gitignore"))
        report["checks"]["gitignore"] = has_gitignore
        if not has_gitignore:
            report["score"] -= 10
            report["warnings"].append("Ausência de arquivo .gitignore (risco de lixo no histórico).")

        # 2. CI/CD Presence
        has_github_actions = os.path.isdir(os.path.join(repo_path, ".github", "workflows"))
        has_gitlab_ci = os.path.exists(os.path.join(repo_path, ".gitlab-ci.yml"))
        has_ci = has_github_actions or has_gitlab_ci
        report["checks"]["ci_cd"] = has_ci
        if not has_ci:
            report["score"] -= 10
            report["warnings"].append("Ausência de pipeline de CI/CD detectável (.github ou .gitlab-ci).")

        # 3. Community / Governance Docs
        has_codeowners = any(os.path.exists(os.path.join(repo_path, f)) for f in ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"])
        report["checks"]["codeowners"] = has_codeowners
        if not has_codeowners:
            report["score"] -= 5

        has_contributing = any(os.path.exists(os.path.join(repo_path, f)) for f in ["CONTRIBUTING.md", "contributing.md"])
        report["checks"]["contributing"] = has_contributing
        if not has_contributing:
            report["score"] -= 5

        has_security = any(os.path.exists(os.path.join(repo_path, f)) for f in ["SECURITY.md", "security.md"])
        report["checks"]["security"] = has_security
        if not has_security:
            report["score"] -= 5

        # Se faltar qualquer doc de governança open source, gera warning condensado
        if not (has_codeowners and has_contributing and has_security):
            report["warnings"].append("Faltam arquivos de Governança (CODEOWNERS, CONTRIBUTING.md ou SECURITY.md).")

        # 4. Critical Security Risks (.env check)
        # Verify if .env is tracked by git (not just existing on disk)
        import subprocess
        
        if not os.path.isdir(repo_path) or not os.path.exists(os.path.join(repo_path, ".git")):
            return report

        try:
            res = subprocess.run(["git", "ls-files", ".env"], cwd=repo_path, capture_output=True, text=True, timeout=15)
            is_env_tracked = res.stdout.strip() != ""
        except Exception:
            is_env_tracked = False
        report["checks"]["env_exposed"] = is_env_tracked

        if is_env_tracked:
            report["score"] -= 50
            report["critical"].append("CRÍTICO: O arquivo '.env' está versionado no repositório! Risco de vazamento de credenciais.")

        # Floor score at 0
        if report["score"] < 0:
            report["score"] = 0

        return report
