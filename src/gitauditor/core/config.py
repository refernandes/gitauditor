import json
import os

CONFIG_DIR = os.path.expanduser("~/.gitauditor")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


class ConfigManager:
    @staticmethod
    def get_default_config():
        return {
            "ai": {
                "provider": "ollama",
                "model": "llama3",
                "api_key": "",
                "base_url": "http://localhost:11434",
            }
        }

    @staticmethod
    def load_config() -> dict:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)

        if not os.path.exists(CONFIG_FILE):
            config = ConfigManager.get_default_config()
            ConfigManager.save_config(config)
            return config

        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return ConfigManager.get_default_config()

    @staticmethod
    def save_config(config: dict):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        # Security: ensure config.json is only readable/writable by the owner
        # since it stores sensitive API keys
        if hasattr(os, "chmod"):
            try:
                os.chmod(CONFIG_FILE, 0o600)
            except Exception:
                pass
