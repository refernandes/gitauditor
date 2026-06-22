import asyncio
import re


def parse_remote_url(remote_url: str):
    """Extrai host, owner, repo_name e canonical_name da URL."""
    host = None
    owner = None
    canonical_name = None

    if remote_url:
        ssh_match = re.match(r"^git@([^:]+):([^/]+)/(.+?)(\.git)?$", remote_url)
        https_match = re.match(r"^https?://([^/]+)/([^/]+)/(.+?)(\.git)?$", remote_url)

        match = ssh_match or https_match
        if match:
            host = match.group(1)
            owner = match.group(2)
            repo_name = match.group(3)
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]

            canonical_name = f"{host}/{owner}/{repo_name}"

    return host, owner, canonical_name


async def get_repo_metadata(path: str):
    """Extrai informações do repositório como URL remota, host e owner."""
    remote_url = None
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "remote",
            "get-url",
            "origin",
            cwd=path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            remote_url = stdout.decode().strip()
    except Exception:
        pass

    host, owner, canonical_name = parse_remote_url(remote_url)

    # Todo: calcular size_mb no futuro

    return {
        "path": path,
        "remote_url": remote_url,
        "host": host,
        "owner": owner,
        "canonical_name": canonical_name,
        "status": "OK" if remote_url else "Orphan",  # Orphan = sem origin
    }


async def enrich_all(paths: list[str]):
    """Enriquece metadados para uma lista de diretórios em paralelo."""
    tasks = [get_repo_metadata(p) for p in paths]
    return await asyncio.gather(*tasks)
