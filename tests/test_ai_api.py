from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gitauditor.core.ai_api import AIClient


@pytest.fixture
def override_config():
    with patch("gitauditor.core.config.ConfigManager.load_config") as mock_load:
        mock_load.return_value = {
            "ai": {"provider": "ollama", "model": "llama3", "base_url": "http://localhost:11434"}
        }
        yield mock_load


@pytest.mark.asyncio
async def test_generate_structured_success(override_config):
    """Teste envio de prompt base retorna json válido."""
    client = AIClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": '{"test": "valid"}'}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await client._generate_structured("test prompt", {"type": "object"})

        assert mock_post.called
        assert result == {"test": "valid"}


@pytest.mark.asyncio
async def test_generate_structured_retry_on_error(override_config):
    """Teste tratamento de erro/timeout gracefully (tenacity retries)."""
    client = AIClient()

    mock_response_error = MagicMock()
    mock_response_error.status_code = 500
    mock_response_error.text = "Internal Server Error"

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {"response": '{"recovered": true}'}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [Exception("Timeout"), mock_response_error, mock_response_success]

        result = await client._generate_structured("test prompt", {"type": "object"})

        assert mock_post.call_count == 3
        assert result == {"recovered": True}
