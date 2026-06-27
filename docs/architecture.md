# Architecture

GitAuditor is structured around several core components:

## Core Modules

- **CLI (`cli.py`, `commands/`)**: Uses `typer` to provide a robust command-line interface. State is managed via `typer.Context` and an `AppState` object.
- **Catalog (`catalog_db.py`, `models.py`)**: Uses `sqlmodel` for local SQLite database management. Tracks cloned repositories and configuration.
- **AI Engine (`ai_api.py`)**: An abstraction layer for talking to multiple LLM providers (OpenAI, OpenRouter, Azure, Ollama).
- **Scanner (`scanner.py`)**: Handles Git parsing and semantic extraction (hash calculation, tree generation).
- **Policy Engine (`policy_engine.py`)**: Applies security and standard rules across repositories.
- **Worktree Manager**: Orchestrates linked Git worktrees for efficient multi-branch development without full clones.
