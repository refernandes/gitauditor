# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions workflow for MkDocs deployment (Phase 5).
- Comprehensive metadata to `pyproject.toml`.
- Docstrings across public modules (`ai_api.py`, `policy_engine.py`, `scanner.py`, `models.py`).

## [3.0.0] - 2026-06-27

### Added
- **Semantic Catalog (P3 Blueprint)**: Transformed into an AI-powered Intelligent Code Infrastructure Catalog.
- **Git Worktree Manager (P2)**: Created linked worktrees for efficient branch management.
- Multi-provider AI configuration panel (OpenAI, OpenRouter, Ollama, Azure).
- Semantic context extraction (hash-based project tree analysis).
- Auto-tagging system (heuristic + AI).
- Local strict code reviewer.
- AI-generated release notes (`gitauditor repo changelog`).

## [2.0.0] - 2025-10-15

### Added
- SQLite local database via `SQLModel` (`~/.gitauditor/catalog.db`).
- Improved repository discovery and deduplication.

### Changed
- Refactored core modules for better testability.

## [1.0.0] - 2025-01-10

### Added
- Initial release.
- Basic CLI structure using `Typer` and `Rich`.
- Local script capabilities to scan repositories.
