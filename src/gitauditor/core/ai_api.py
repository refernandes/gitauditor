"""
AI Provider integration module.

Provides a unified interface (AIClient) to communicate with different LLM
providers (OpenAI, OpenRouter, Azure, Ollama) and enforces structured JSON
outputs for semantic analysis tasks.
"""

import json

import httpx
from rich import print
from tenacity import retry, stop_after_attempt, wait_exponential

from gitauditor.core.audit_log import AuditLogger
from gitauditor.core.config import ConfigManager
from gitauditor.core.exceptions import AIProviderError


class AIClient:
    """
    Unified client for interacting with AI models across different providers.

    Handles configuration, retries, timeouts, and structured JSON parsing.
    Supports local (Ollama) and cloud (OpenAI, OpenRouter, Azure) endpoints.
    """

    def __init__(self):
        config = ConfigManager.load_config()
        self.ai_config = config.get("ai", {})
        self.provider = self.ai_config.get("provider", "ollama").lower()
        self.model = self.ai_config.get("model", "llama3")
        self.api_key = self.ai_config.get("api_key", "")

        # Default base URLs
        if self.provider == "ollama":
            self.base_url = self.ai_config.get("base_url", "http://localhost:11434")
        elif self.provider == "openai":
            self.base_url = self.ai_config.get("base_url", "https://api.openai.com/v1")
        elif self.provider == "openrouter":
            self.base_url = self.ai_config.get("base_url", "https://openrouter.ai/api/v1")
        elif self.provider == "azure":
            self.base_url = self.ai_config.get(
                "base_url", "https://<your-resource>.services.ai.azure.com/openai/v1"
            )
        else:
            self.base_url = self.ai_config.get("base_url", "")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry_error_callback=lambda s: (
            print(f"\n[bold red]Erro do LLM:[/bold red] {s.outcome.exception()}") or None
        ),
    )
    async def _generate_structured(
        self, prompt: str, schema_dict: dict, timeout: float = 120.0
    ) -> dict | None:
        """
        Unified method to request structured JSON from different providers.
        Retries up to 3 times on failure.
        """
        async with httpx.AsyncClient(timeout=timeout) as client:
            if self.provider == "ollama":
                # Ollama direct generate endpoint
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": schema_dict,
                    },
                )
                if response.status_code == 200:
                    raw = response.json().get("response", "{}").strip()
                    raw = raw.removeprefix("```json").removesuffix("```").strip()
                    raw = raw.removeprefix("```").strip()
                    return json.loads(raw)
                if response.status_code != 200:
                    raise AIProviderError(
                        f"Ollama API Error: {response.status_code} - {response.text}"
                    )

            else:
                # OpenAI / OpenRouter / Azure Chat Completions API
                headers = {
                    "Content-Type": "application/json",
                }

                if self.provider == "azure" and self.api_key == "azure_default_credential":
                    from azure.identity import DefaultAzureCredential

                    credential = DefaultAzureCredential()
                    token = credential.get_token("https://ai.azure.com/.default").token
                    headers["Authorization"] = f"Bearer {token}"
                else:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                if self.provider == "openrouter":
                    headers["HTTP-Referer"] = "https://github.com/gitauditor"
                    headers["X-Title"] = "GitAuditor"

                # Appending schema to prompt to enforce JSON shape
                # (since some OpenRouter models don't support response_format strict)
                system_msg = (
                    "You must respond ONLY with a valid JSON object matching this schema:\n"
                    f"{json.dumps(schema_dict)}\n"
                    "Do not include markdown blocks or any other text."
                )

                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                }

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    raw = data["choices"][0]["message"]["content"].strip()
                    raw = raw.removeprefix("```json").removesuffix("```").strip()
                    raw = raw.removeprefix("```").strip()
                    return json.loads(raw)
                if response.status_code != 200:
                    raise AIProviderError(f"API Error: {response.status_code} - {response.text}")

    # ---------------------------------------------------------
    # GITAUDITOR SEMANTIC FEATURES
    # ---------------------------------------------------------

    async def analyze_commit_message(self, commit_msg: str, diff_text: str) -> str | None:
        prompt = (
            "You are an expert Git hook enforcing conventional commits.\n"
            f"Original Message: {commit_msg}\n\n"
            f"DIFF:\n{diff_text}\n\n"
            "Rewrite the commit message using conventional commits (feat, fix, refactor, etc.). "
            "Respond ONLY with a JSON object containing a 'suggested_message' field."
        )
        schema = {
            "type": "object",
            "properties": {"suggested_message": {"type": "string"}},
        }
        res = await self._generate_structured(prompt, schema, timeout=30.0)

        status = "SUCCESS" if res else "ERROR"
        AuditLogger.log(
            command="ai_amend",
            status=status,
            summary="Gerou nova mensagem de commit com base no diff.",
            ai_provider=self.provider,
            ai_model=self.model,
            details=json.dumps(res) if res else "RetryError or Invalid Response",
        )

        return res.get("suggested_message") if res else None

    async def analyze_repo_semantics(self, context_str: str) -> dict | None:
        from gitauditor.core.semantic import RepoSummarySchema

        prompt = (
            "You are an expert software architect analyzing a repository.\n"
            "Based on the repository context below (Tree, Manifests, README), extract a short summary, "
            "the tech stack list, suggested tags, and the risk/activity level.\n\n"
            f"CONTEXT:\n{context_str}\n"
        )
        res = await self._generate_structured(prompt, RepoSummarySchema.model_json_schema())

        status = "SUCCESS" if res else "ERROR"
        AuditLogger.log(
            command="ai_summarize",
            status=status,
            summary="Resumiu arquitetura do repositório.",
            ai_provider=self.provider,
            ai_model=self.model,
        )
        return res

    async def refine_repo_tags(
        self, context_str: str, heuristic_tags: list[str]
    ) -> list[str] | None:
        from gitauditor.core.semantic import RepoTagSchema

        prompt = (
            "You are an expert software architect analyzing a repository.\n"
            f"A deterministic scanner suggested these base tags for the project: {heuristic_tags}\n"
            "Based on the repository context below, refine or add new tags that represent the main stack, purpose, and category of this project.\n\n"
            f"CONTEXT:\n{context_str}\n"
        )
        res = await self._generate_structured(prompt, RepoTagSchema.model_json_schema())

        status = "SUCCESS" if res else "ERROR"
        AuditLogger.log(
            command="ai_tagging",
            status=status,
            summary="Refinou tags heurísticas com IA.",
            ai_provider=self.provider,
            ai_model=self.model,
        )
        return res.get("tags", heuristic_tags) if res else heuristic_tags

    async def analyze_local_diff(self, diff_content: str) -> dict | None:
        from gitauditor.core.semantic import RepoReviewSchema

        prompt = (
            "You are a strict and senior software reviewer.\n"
            "Review the following code diff for code smells, anti-patterns, and architectural risks. "
            "Do NOT focus on secrets.\n\n"
            f"DIFF:\n{diff_content}\n"
        )
        res = await self._generate_structured(prompt, RepoReviewSchema.model_json_schema())

        status = "SUCCESS" if res else "ERROR"
        AuditLogger.log(
            command="ai_review",
            status=status,
            summary="Realizou code review no diff atual.",
            ai_provider=self.provider,
            ai_model=self.model,
        )
        return res

    async def generate_changelog(self, commits_log: str) -> dict | None:
        from gitauditor.core.semantic import RepoChangelogSchema

        prompt = (
            "You are an expert technical writer and release manager.\n"
            "Analyze the following list of git commits and generate a structured human-readable changelog/release notes.\n"
            "Group the information into features, fixes, and breaking changes. Summarize the overall evolution.\n\n"
            f"COMMITS LOG:\n{commits_log}\n"
        )
        res = await self._generate_structured(prompt, RepoChangelogSchema.model_json_schema())

        status = "SUCCESS" if res else "ERROR"
        AuditLogger.log(
            command="ai_changelog",
            status=status,
            summary="Gerou changelog a partir dos commits.",
            ai_provider=self.provider,
            ai_model=self.model,
        )
        return res
