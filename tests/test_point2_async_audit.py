import pytest
import asyncio
import time
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.cli import GitAuditorCLI

@pytest.mark.asyncio
async def test_audit_all_repos_is_concurrent():
    """Garante que a auditoria de repositórios executa de forma paralela e assíncrona."""
    cli = GitAuditorCLI()
    
    # Simula 10 repositórios
    cli.repos = [f"/fake/repo_{i}" for i in range(10)]
    
    # Mock do create_subprocess_exec
    # Cada chamada vai demorar 0.2 segundos
    async def mock_subprocess(*args, **kwargs):
        await asyncio.sleep(0.2)
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"up-to-date")
        return mock_proc

    start_time = time.time()
    
    with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
        # A chamada precisa ser awaitable
        await cli._audit_all_repos()
        
    duration = time.time() - start_time
    
    # Se fosse sequencial, 10 * 0.2 = 2.0 segundos.
    # Sendo paralelo, deve demorar pouco mais de 0.2 segundos.
    assert duration < 0.5, f"Auditoria demorou {duration}s, não parece estar paralela!"
    
    # Verifica que todos os 10 repositórios receberam status
    assert len(cli.repo_status) == 10
    for i in range(10):
        assert cli.repo_status[f"/fake/repo_{i}"]["icon"] == "🟢 OK"
