import os

import git

from .exceptions import ScanError


class GitService:
    """Serviço para interagir com repositórios Git usando GitPython."""

    @staticmethod
    def _sanitize_hash(commit_hash: str) -> str:
        """Sanitiza strings de hash para evitar injection no GitPython (--flag ou shell)."""
        import re
        if not commit_hash or not isinstance(commit_hash, str):
            return "HEAD"
        # Permite alfanuméricos, ~, ^, mas proíbe espaços, ; e duplos hifens
        s = re.sub(r"[^a-zA-Z0-9~^\-]", "", commit_hash)
        if "--" in s:
            raise ScanError("Invalid commit hash format")
        return s

    @staticmethod
    def get_repo_details(path: str) -> dict:
        """Obtém detalhes de um repositório."""
        try:
            repo = git.Repo(path)

            # Info básica
            current_branch = (
                repo.active_branch.name
                if not repo.head.is_detached
                else "Detached HEAD"
            )
            remote_url = (
                repo.remotes.origin.url
                if "origin" in repo.remotes
                else "Sem remote 'origin'"
            )

            # Status
            is_dirty = repo.is_dirty()

            # Commits recentes (últimos 500 para suportar paginação)
            commits = []
            try:
                for commit in repo.iter_commits(current_branch, max_count=500):
                    commits.append(
                        {
                            "hash": commit.hexsha[:7],
                            "message": commit.message.strip(),
                            "author": commit.author.name,
                            "date": commit.authored_datetime.strftime("%Y-%m-%d %H:%M"),
                        }
                    )
            except Exception:
                pass  # Possivelmente repo vazio

            return {
                "name": os.path.basename(path),
                "path": path,
                "branch": current_branch,
                "remote": remote_url,
                "is_dirty": is_dirty,
                "commits": commits,
                "user_name": repo.config_reader().get_value(
                    "user", "name", "Não configurado"
                ),
                "user_email": repo.config_reader().get_value(
                    "user", "email", "Não configurado"
                ),
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def amend_commit_message(path: str, new_message: str):
        """Atualiza a mensagem do último commit (amend), redefinindo o autor para o configurado localmente."""
        repo = git.Repo(path)
        repo.git.commit("--amend", "-m", new_message, "--reset-author")

    @staticmethod
    def get_commit_diff(path: str, commit_hash: str = "HEAD") -> str:
        """Obtém o diff de um commit específico (padrão HEAD)."""
        commit_hash = GitService._sanitize_hash(commit_hash)
        repo = git.Repo(path)
        try:
            return repo.git.show(commit_hash, "--stat", "--patch")
        except Exception:
            return "Não foi possível obter o diff."

    @staticmethod
    def is_rebasing(path: str) -> bool:
        """Verifica se o repositório está no meio de um rebase."""
        rebase_merge = os.path.join(path, ".git", "rebase-merge")
        rebase_apply = os.path.join(path, ".git", "rebase-apply")
        return os.path.exists(rebase_merge) or os.path.exists(rebase_apply)

    @staticmethod
    def start_interactive_rebase(path: str, commits_count: int = 5):
        """Inicia um rebase iterativo parando (edit) nos últimos N commits."""
        import subprocess
        import tempfile

        # Cria um script Python para substituir o 'sed' e manter compatibilidade com Windows/Linux/Mac
        seq_editor_fd, seq_editor_path = tempfile.mkstemp(text=True)
        os.close(seq_editor_fd)

        try:
            with open(seq_editor_path, "w") as f:
                f.write("""#!/usr/bin/env python3
import sys
with open(sys.argv[1], "r") as file:
    lines = file.readlines()
with open(sys.argv[1], "w") as file:
    for line in lines:
        if line.startswith("pick "):
            line = line.replace("pick ", "edit ", 1)
        file.write(line)
""")
            os.chmod(seq_editor_path, 0o755)

            env = os.environ.copy()
            env["GIT_SEQUENCE_EDITOR"] = seq_editor_path

            subprocess.run(
                ["git", "rebase", "-i", "--rebase-merges", f"HEAD~{commits_count}"],
                cwd=path,
                env=env,
                check=True,
                capture_output=True,
                timeout=15,
            )
        except subprocess.CalledProcessError as e:
            raise ScanError(f"Erro ao iniciar rebase: {e.stderr.decode()}")
        finally:
            if os.path.exists(seq_editor_path):
                os.remove(seq_editor_path)

    @staticmethod
    def abort_rebase(path: str):
        repo = git.Repo(path)
        try:
            repo.git.rebase("--abort")
        except Exception:
            pass

    @staticmethod
    def continue_rebase(path: str):
        """Continua o processo de rebase."""
        import subprocess

        env = os.environ.copy()
        # Evitar abrir o editor de texto ao continuar
        env["GIT_EDITOR"] = "true"
        try:
            subprocess.run(
                ["git", "rebase", "--continue"], cwd=path, env=env, capture_output=True, timeout=15
            )
        except Exception:
            pass

    @staticmethod
    def get_latest_commit_info(path: str) -> dict:
        """Obtém metadados (data e mensagem) do último commit para desempate de duplicados."""
        info = {"date": "1970-01-01 00:00", "message": "N/A"}
        try:
            repo = git.Repo(path)
            if repo.head.is_valid():
                c = repo.head.commit
                info["date"] = c.authored_datetime.strftime("%Y-%m-%d %H:%M")
                info["message"] = c.message.strip().split("\n")[0][:50]
        except Exception:
            pass
        return info

    @staticmethod
    def find_open_branches(path: str) -> list[str]:
        """Verifica branches locais existentes."""
        try:
            repo = git.Repo(path)
            return [b.name for b in repo.branches]
        except Exception:
            return []

    @staticmethod
    def extract_diff_for_commit(path: str, commit_hash: str) -> str:
        """Isola o diff *exato* de um commit no histórico."""
        commit_hash = GitService._sanitize_hash(commit_hash)
        repo = git.Repo(path)
        try:
            # Pega as estatísticas e as mudanças do commit em relação ao seu pai
            res = repo.git.show(commit_hash, "--stat", "--patch")
            if not res or res.strip() == "":
                return f"Não foi possível obter o diff. O retorno do git show foi VAZIO para o hash {commit_hash}."
            return res
        except Exception as e:
            return f"Não foi possível obter o diff. Detalhe do Git: {repr(e)}"

    @staticmethod
    def reword_commit(path: str, commit_hash: str, new_message: str) -> bool:
        """Muda a mensagem de um commit antigo (mesmo longe no histórico) usando rebase interativo."""
        commit_hash = GitService._sanitize_hash(commit_hash)
        import subprocess
        import tempfile

        # Cria scripts Python temporários para atuar como editores não-interativos do Git
        seq_editor_fd, seq_editor_path = tempfile.mkstemp(text=True)
        msg_editor_fd, msg_editor_path = tempfile.mkstemp(text=True)

        msg_text_fd, msg_text_path = tempfile.mkstemp(text=True)

        # Fecha os file descriptors baixos imediatamente para evitar erro "Text file busy" no Linux
        os.close(seq_editor_fd)
        os.close(msg_editor_fd)
        os.close(msg_text_fd)

        repo = git.Repo(path)
        commit_obj = repo.commit(commit_hash)

        # GUARDRAIL: Create a backup branch for rollback before destructive rebase
        import datetime
        backup_branch_name = f"gitauditor-backup-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}-{commit_hash[:7]}"
        try:
            repo.create_head(backup_branch_name, "HEAD")
        except Exception:
            pass # Ignore if it fails, just a safety measure

        try:
            # 1. Script para alterar a instrução do rebase ('pick' para 'reword') no commit alvo
            with open(seq_editor_path, "w") as f:
                f.write(f'''#!/usr/bin/env python3
import sys
with open(sys.argv[1], "r") as file:
    lines = file.readlines()
with open(sys.argv[1], "w") as file:
    for line in lines:
        if line.startswith("pick ") and "{commit_hash[:7]}" in line:
            line = line.replace("pick ", "reword ", 1)
        file.write(line)
''')
            os.chmod(seq_editor_path, 0o755)

            # 2. Escreve a nova mensagem em um txt seguro (Evita code injection no script Python)
            with open(msg_text_path, "w", encoding="utf-8") as f:
                f.write(new_message)

            # 3. Script para ler o arquivo txt seguro e gravar no GIT_EDITOR
            with open(msg_editor_path, "w") as f:
                f.write(f'''#!/usr/bin/env python3
import sys
import shutil
shutil.copy("{msg_text_path}", sys.argv[1])
''')
            os.chmod(msg_editor_path, 0o755)

            env = os.environ.copy()
            env["GIT_SEQUENCE_EDITOR"] = seq_editor_path
            env["GIT_EDITOR"] = msg_editor_path

            # Inicia o rebase, usando autostash para evitar que erros de dirty-tree bloqueiem o processo
            if not commit_obj.parents:
                subprocess.run(
                    ["git", "rebase", "-i", "--rebase-merges", "--autostash", "--root"],
                    cwd=path,
                    env=env,
                    check=True,
                    capture_output=True,
                    timeout=15,
                )
            else:
                subprocess.run(
                    [
                        "git",
                        "rebase",
                        "-i",
                        "--rebase-merges",
                        "--autostash",
                        f"{commit_hash}^",
                    ],
                    cwd=path,
                    env=env,
                    check=True,
                    capture_output=True,
                    timeout=15,
                )

            return backup_branch_name
        except subprocess.CalledProcessError as e:
            subprocess.run(["git", "rebase", "--abort"], cwd=path, capture_output=True, timeout=15)
            raise Exception(f"Rebase failed: {e.stderr.decode()}")
        finally:
            if os.path.exists(seq_editor_path):
                os.remove(seq_editor_path)
            if os.path.exists(msg_editor_path):
                os.remove(msg_editor_path)
            if os.path.exists(msg_text_path):
                os.remove(msg_text_path)

    @staticmethod
    def rollback_amend(path: str, backup_branch: str) -> bool:
        """Restaura o histórico a partir de uma branch de backup e deleta a branch."""
        try:
            repo = git.Repo(path)
            repo.git.reset("--hard", backup_branch)
            repo.delete_head(backup_branch, force=True)
            return True
        except Exception as e:
            raise ScanError(f"Erro no rollback: {e}")
