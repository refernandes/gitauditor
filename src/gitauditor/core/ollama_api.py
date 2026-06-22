import httpx
import json
import os
import hashlib
from typing import Optional


class OllamaClient:
    """Cliente para interagir com o Ollama local."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        self.cache_file = os.path.expanduser("~/.gitauditor_ai_cache.json")
        self._load_cache()

    def _load_cache(self):
        self.cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
            except Exception:
                pass

    def _save_cache(self):
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception:
            pass

    async def suggest_commit_message(self, diff: str) -> Optional[str]:
        """Envia um diff para o Ollama e solicita uma mensagem convencional."""

        # Cria hash do diff para usar como chave de cache (Memória Curta/Longa)
        diff_hash = hashlib.sha256(diff.encode("utf-8", errors="ignore")).hexdigest()

        if diff_hash in self.cache:
            return self.cache[diff_hash]

        prompt = (
            "Abaixo está o diff de um commit Git. "
            "Sugira uma mensagem de commit curta e concisa seguindo o padrão Conventional Commits (ex: feat: add logging). "
            "Responda APENAS com a mensagem sugerida, sem explicações.\n\n"
            f"DIFF:\n{diff[:2000]}"  # Limitando o tamanho do diff para o prompt
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )

                if response.status_code == 200:
                    data = response.json()
                    suggestion = data.get("response", "").strip()

                    # Salva no cache
                    self.cache[diff_hash] = suggestion
                    self._save_cache()

                    return suggestion
                else:
                    return f"Erro Ollama: Status {response.status_code}"
        except Exception as e:
            return f"Erro Ollama/HTTP: {repr(e)}"

    async def analyze_repo_semantics(self, context_str: str) -> Optional[dict]:
        """
        P3: Faz análise estruturada de um repositório forçando a resposta JSON
        usando o Schema do Pydantic no parâmetro format.
        """
        from gitauditor.core.semantic import RepoSummarySchema

        prompt = (
            "You are an expert software architect analyzing a repository structure.\n"
            "Based on the following repository context (file tree, manifests, and README), "
            "generate a concise JSON summary adhering strictly to the provided JSON schema.\n\n"
            f"CONTEXT:\n{context_str}\n"
        )

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": RepoSummarySchema.model_json_schema(),
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    raw_json = data.get("response", "{}").strip()
                    try:
                        # Validate and parse directly
                        return json.loads(raw_json)
                    except Exception:
                        return None
                else:
                    return None
        except Exception:
            return None
