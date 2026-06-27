import glob
import os
import subprocess


class IdentityManager:
    """Gerencia e audita identidades Git e chaves SSH."""

    @staticmethod
    def get_global_git_config() -> dict[str, str]:
        """Obtém as configurações globais de usuário do Git."""
        configs = {"name": "Não configurado", "email": "Não configurado"}
        try:
            name_result = subprocess.run(
                ["git", "config", "--global", "user.name"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if name_result.returncode == 0 and name_result.stdout.strip():
                configs["name"] = name_result.stdout.strip()

            email_result = subprocess.run(
                ["git", "config", "--global", "user.email"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if email_result.returncode == 0 and email_result.stdout.strip():
                configs["email"] = email_result.stdout.strip()
        except Exception:
            pass
        return configs

    @staticmethod
    def list_ssh_keys() -> list[dict[str, str]]:
        """Lista as chaves SSH na pasta ~/.ssh do usuário."""
        ssh_dir = os.path.expanduser("~/.ssh")
        keys = []
        if not os.path.exists(ssh_dir):
            return keys

        # Procura por arquivos de chave pública comuns (.pub)
        pub_keys = glob.glob(os.path.join(ssh_dir, "*.pub"))

        for pub_key in pub_keys:
            private_key = pub_key[:-4]  # Remove o .pub
            if os.path.exists(private_key):
                key_type = "Unknown"
                if "rsa" in private_key:
                    key_type = "RSA"
                elif "ed25519" in private_key:
                    key_type = "Ed25519"
                elif "ecdsa" in private_key:
                    key_type = "ECDSA"

                keys.append(
                    {
                        "name": os.path.basename(private_key),
                        "path": private_key,
                        "type": key_type,
                    }
                )
        return keys

    @staticmethod
    def set_repo_identity(
        repo_path: str, ssh_key_path: str = None, name: str = None, email: str = None
    ) -> bool:
        """Configura a identidade local e a chave SSH para um repositório específico."""
        try:
            if name:
                subprocess.run(
                    ["git", "config", "user.name", name], cwd=repo_path, check=True, timeout=15
                )
            if email:
                subprocess.run(
                    ["git", "config", "user.email", email], cwd=repo_path, check=True, timeout=15
                )
            if ssh_key_path:
                # Usa core.sshCommand para forçar o Git a usar uma chave SSH específica
                ssh_command = f"ssh -i {ssh_key_path} -F /dev/null"
                subprocess.run(
                    ["git", "config", "core.sshCommand", ssh_command],
                    cwd=repo_path,
                    check=True,
                    timeout=15,
                )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    async def test_provider_connection(provider: str = "github.com") -> bool:
        """Testa se há conexão SSH válida com um provedor (ex: git@github.com)."""
        import asyncio

        # Cria o processo subprocess para testar a conexão SSH
        # ssh -T git@github.com normalmente retorna 1 com a msg de sucesso se autenticar,
        # ou 255 se Permission denied.
        try:
            process = await asyncio.create_subprocess_exec(
                "ssh",
                "-T",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ConnectTimeout=5",
                f"git@{provider}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            output = stderr.decode() + stdout.decode()

            # Github e Gitlab retornam mensagens de boas vindas no stderr
            if "successfully authenticated" in output.lower() or "welcome" in output.lower():
                return True
            return False
        except Exception:
            return False
