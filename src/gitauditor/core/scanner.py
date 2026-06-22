import os
import asyncio
from typing import List

# Reutilizando a lista de diretórios ignorados do seu script original
IGNORED_DIRS = {
    "node_modules",
    ".cache",
    "venv",
    "env",
    ".env",
    "build",
    "target",
    "dist",
    ".tox",
    ".rustup",
    ".cargo",
    "__pycache__",
    ".idea",
    ".vscode",
    "proc",
    "sys",
    "dev",
    "run",
    "boot",
    "tmp",
    "var",
    "snap",
    "Windows",
    "Program Files",
    "Program Files (x86)",
    "AppData",
    "$RECYCLE.BIN",
    "System Volume Information",
}


class GitScanner:
    """Serviço assíncrono para varredura de repositórios Git."""

    def __init__(self, callback=None):
        self.found_repos = []
        self.is_scanning = False
        self.callback = callback  # Função chamada a cada repo encontrado
        self.semaphore = asyncio.Semaphore(4)  # Limite de 4 raízes concorrentes

    async def scan(self, root_dirs: List[str]) -> List[str]:
        """Inicia a varredura assíncrona nos diretórios raiz fornecidos."""
        self.is_scanning = True
        self.found_repos = []

        # Cria tarefas para cada raiz (ex: discos diferentes no Windows ou pastas no Linux)
        tasks = [self._scan_dir(d) for d in root_dirs]
        await asyncio.gather(*tasks)

        self.is_scanning = False
        return self.found_repos

    async def _scan_dir(self, directory: str):
        """Varre um diretório recursivamente de forma assíncrona com controle de concorrência."""
        if not os.path.exists(directory):
            return

        async with self.semaphore:
            try:
                # Usamos to_thread para não travar o loop de eventos com I/O de disco
                await asyncio.to_thread(self._sync_walk, directory)
            except Exception:
                # Ignora erros de permissão ou pastas inacessíveis
                pass

    def _sync_walk(self, directory: str):
        """Executa o walk de forma síncrona dentro de uma thread separada."""
        for root, dirs, files in os.walk(directory, topdown=True):
            # Filtra in-place para eficiência
            dirs[:] = [
                d
                for d in dirs
                if d not in IGNORED_DIRS and (not d.startswith(".") or d == ".git")
            ]

            if ".git" in dirs:
                full_path = os.path.abspath(root)
                self.found_repos.append(full_path)
                if self.callback:
                    # O callback precisa lidar com a thread se for atualizar UI
                    self.callback(full_path)
                dirs.remove(".git")  # Não entra dentro da pasta .git
