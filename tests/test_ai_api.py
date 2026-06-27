import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from gitauditor.core.ai_api import AIClient
from gitauditor.core.exceptions import AIProviderError

# Dummy schemas
DUMMY_SCHEMA = {
    "type": "object",
    "properties": {"result": {"type": "string"}},
}

@pytest.fixture
def override_config():
    with patch("gitauditor.core.config.ConfigManager.load_config") as mock_load:
        mock_load.return_value = {
            "ai": {
                "provider": "ollama",
                "model": "llama3",
                "base_url": "http://localhost:11434"
            }
        }
        yield mock_load

@pytest.mark.asyncio
async def test_generate_structured_success(override_config):
    """Teste envio de prompt base retorna json válido."""
    client = AIClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": '```json\n{"test": "valid"}\n```'}

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

        # Use patch on sleep so tests are fast
        with patch("tenacity.nap.time.sleep"):
            result = await client._generate_structured("test prompt", {"type": "object"})

        assert mock_post.call_count == 3
        assert result == {"recovered": True}

@pytest.mark.asyncio
async def test_openai_generate_success(override_config):
    override_config.return_value = {
        "ai": {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-test"
        }
    }
    client = AIClient()
    assert client.provider == "openai"
    assert client.base_url == "https://api.openai.com/v1"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '```json\n{"result": "success"}\n```'}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        result = await client._generate_structured("test prompt", DUMMY_SCHEMA)
        
        assert result == {"result": "success"}
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "Authorization" in kwargs["headers"]
        assert kwargs["headers"]["Authorization"] == "Bearer sk-test"

@pytest.mark.asyncio
async def test_openai_generate_failure(override_config):
    override_config.return_value = {
        "ai": {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-test"
        }
    }
    client = AIClient()

    mock_response_error = MagicMock()
    mock_response_error.status_code = 500
    mock_response_error.text = "Internal Server Error"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response_error
        
        with patch("tenacity.nap.time.sleep"):
            result = await client._generate_structured("test prompt", DUMMY_SCHEMA)
            assert result is None

@pytest.mark.asyncio
async def test_azure_generate_with_default_credential(override_config):
    override_config.return_value = {
        "ai": {
            "provider": "azure",
            "model": "gpt-4o",
            "api_key": "azure_default_credential",
            "base_url": "https://test.services.ai.azure.com/openai/v1"
        }
    }
    client = AIClient()
    assert client.provider == "azure"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"result": "success"}'}}]
    }

    mock_credential_instance = MagicMock()
    mock_credential_instance.get_token.return_value = MagicMock(token="fake-azure-token")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with patch("azure.identity.DefaultAzureCredential", return_value=mock_credential_instance):
            result = await client._generate_structured("test prompt", DUMMY_SCHEMA)
            
            assert result == {"result": "success"}
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert kwargs["headers"]["Authorization"] == "Bearer fake-azure-token"

@pytest.mark.asyncio
async def test_analyze_commit_message(override_config):
    client = AIClient()
    with patch.object(client, "_generate_structured", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"suggested_message": "feat: test"}
        with patch("gitauditor.core.audit_log.AuditLogger.log"):
            res = await client.analyze_commit_message("msg", "diff")
            assert res == "feat: test"

@pytest.mark.asyncio
async def test_analyze_repo_semantics(override_config):
    client = AIClient()
    with patch.object(client, "_generate_structured", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"summary": "A cool repo"}
        with patch("gitauditor.core.audit_log.AuditLogger.log"):
            res = await client.analyze_repo_semantics("context")
            assert res == {"summary": "A cool repo"}

@pytest.mark.asyncio
async def test_refine_repo_tags(override_config):
    client = AIClient()
    with patch.object(client, "_generate_structured", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"tags": ["python", "ai"]}
        with patch("gitauditor.core.audit_log.AuditLogger.log"):
            res = await client.refine_repo_tags("context", ["python"])
            assert res == ["python", "ai"]

@pytest.mark.asyncio
async def test_analyze_local_diff(override_config):
    client = AIClient()
    with patch.object(client, "_generate_structured", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"score": 90}
        with patch("gitauditor.core.audit_log.AuditLogger.log"):
            res = await client.analyze_local_diff("diff content")
            assert res == {"score": 90}

@pytest.mark.asyncio
async def test_generate_changelog(override_config):
    client = AIClient()
    with patch.object(client, "_generate_structured", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"features": ["A"]}
        with patch("gitauditor.core.audit_log.AuditLogger.log"):
            res = await client.generate_changelog("commits")
            assert res == {"features": ["A"]}

@pytest.mark.asyncio
async def test_openrouter_and_other_providers(override_config):
    # openrouter
    override_config.return_value = {
        "ai": {
            "provider": "openrouter",
            "model": "gpt-4",
            "api_key": "sk-test"
        }
    }
    client = AIClient()
    assert client.provider == "openrouter"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"result": "success"}'}}]
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client._generate_structured("prompt", DUMMY_SCHEMA)
        assert result == {"result": "success"}
        args, kwargs = mock_post.call_args
        assert kwargs["headers"]["HTTP-Referer"] == "https://github.com/gitauditor"

    # other provider
    override_config.return_value = {
        "ai": {
            "provider": "anthropic",
            "model": "claude",
            "base_url": "custom_url"
        }
    }
    client2 = AIClient()
    assert client2.base_url == "custom_url"
