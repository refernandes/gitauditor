# Configuration

GitAuditor supports multiple AI providers for its semantic features. 

## Setting up Providers

You can configure the active provider using:

```bash
gitauditor config set provider <provider_name>
```

Currently supported providers:
- `openai`
- `ollama` (Local)
- `openrouter`
- `azure`

## Managing Keys

Set API keys for cloud providers:

```bash
gitauditor config set api_key <your_api_key>
```

For custom endpoint configurations (like Azure or Ollama):

```bash
gitauditor config set endpoint_url <url>
```
