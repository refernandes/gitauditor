# GitAuditor 🤖

[![CI](https://github.com/refernandes/gitauditor/actions/workflows/ci.yml/badge.svg)](https://github.com/refernandes/gitauditor/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/refernandes/gitauditor/graph/badge.svg?token=YOUR_TOKEN_HERE)](https://codecov.io/gh/refernandes/gitauditor)
*[Leia esta documentação em Português / Read this in Portuguese](README_pt.md)*

**GitAuditor** has evolved from a simple local script into an **AI-powered Intelligent Code Infrastructure Catalog**.
Built in Python with `Typer`, `SQLModel`, and `Rich`, it transforms repository folders scattered across your machine into a perfectly manageable local database, while understanding the semantic context of your code using AI providers like OpenAI, OpenRouter, or a local Ollama instance.

Stop asking yourself *"Where did I clone that project?"*, *"What is this legacy repository about?"* or *"How do I write release notes for these last 30 commits?"*. GitAuditor automatically maps, catalogs, audits, and analyzes your infrastructure.

---

## 🌟 What's new in Version 3 (The Semantic Catalog)?

The project has undergone an impressive metamorphosis, implementing the **P3 Blueprint (Semantic Layer)** to act as your governance co-pilot:

1. **Efficient Local Database (`SQLModel` + `SQLite`):** Maintains a local catalog (`~/.gitauditor/catalog.db`), loading instantly and deduplicating cloned projects.
2. **Git Worktree Manager (P2):** Creates secure `worktrees` in neighboring folders sharing the same Git history, saving disk space.
3. **Multi-Provider AI Configuration Panel:** Full support for **Ollama** (Local/Free), **OpenAI** (Cloud/High Precision), and **OpenRouter** (Multi-model).
4. **Semantic Context Extraction:** Uses hashes to analyze the project tree and README without wasting CPU, generating summaries (Overview, Tech Stack, Activity Level) using LLMs.
5. **Automatic Classification (Auto-Tagging):** A dual-verification system. It first scans key files (deterministic heuristics) and then uses AI to refine and create business tags (`api`, `frontend`, `monorepo`, etc).
6. **Local Code Review:** A strict reviewer that analyzes your current repository *diff* before the commit, focusing on code smells, architecture, and risks.
7. **Changelog Generator:** Scans the commit history (with a customizable limit) and uses AI to generate structured, human-readable *Release Notes* categorizing Bugs, Features, and Refactors.

---

## 🚀 Installation & Setup

Installing GitAuditor as a CLI package is fully native:

```bash
git clone https://github.com/refernandes/gitauditor.git
cd gitauditor

# Create and activate the virtual environment (Linux/macOS)
python3 -m venv venv
source venv/bin/activate

# Install the app as an interactive package
pip install -e .
```

From now on, the global `gitauditor` command will be available in your terminal!

---

## 🖥️ The Visual Interface (Interactive Mode)

By typing just `gitauditor` in the terminal, you access the interactive UI built with `Rich`. This interface displays a central table with all your repositories and a bottom action menu.

In **Version 3**, the Artificial Intelligence Submenu was added so you can run any tool without memorizing terminal commands:

```text
Menu Principal:
[1] 🔍 View Repository Details
[2] 📂 Search and Open in Editor
[3] 📊 Catalog Health Dashboard
[4] 🧹 Resolve Duplicated Repositories
[5] 🌳 Manage Git Worktrees
[6] 🤖 Artificial Intelligence Tools (V3)
[7] 🔑 Manage SSH Keys and Identities
[8] 🔄 Sync Local Catalog
[9] 🏷️ Filter Table
[0] 🚪 Exit
```

By choosing **Option 6**, you will have access to all the Semantic power over the visual table (the system will ask for the repository ID before running the AI):
- `[1] AI Amend`
- `[2] AI Code Review`
- `[3] AI Changelog`
- `[4] AI Configuration (Change Provider)`
- `[5] AI Auto-Tagging`
- `[6] AI Summarize`

---

## 🛠️ Automation Mode (CLI Commands)

If you prefer scripts or direct commands, all UI options also work via CLI subcommands.

### 1. Configuring your Artificial Intelligence
You can choose which cognitive engine GitAuditor will use (Ollama to run 100% offline, OpenAI or OpenRouter for advanced cloud models).
If you choose **Azure OpenAI**, you must configure your custom resource endpoint (e.g., `https://<your-resource>.services.ai.azure.com/openai/v1`) using the command below.
```bash
gitauditor config
```

### 2. Catalog Synchronization and Health
Before exploring superpowers, populate your machine's database:
```bash
# Map your machine
gitauditor catalog sync

# View overall health (Orphans, Duplicates, Total)
gitauditor catalog health

# Display a normalization plan for duplicated repositories
gitauditor catalog dedupe --plan
```

### 3. The Semantic AI Layer (V3)
Powerful new commands trigger intelligence to interact with your code:

```bash
# Summarize the repository, identify the tech stack, and analyze risks/activity based on the tree and manifests
gitauditor catalog summarize

# Auto-classify the current repository combining local file heuristics with AI analysis
gitauditor catalog tag-auto

# Perform a "Local Code Review" on the current uncommitted diff (code smells and architecture)
gitauditor review

# Generate a professional Changelog from past commits (Default: All, or use limit)
gitauditor changelog --limit 15
```

### 4. AI Amend (The Magic of History Rewriting)
Rewrites your local commit history using your diff to generate new messages following the *Conventional Commits* standard:
```bash
gitauditor amend
```

### 5. Git Worktrees (Saving Disk Space)
Stop cloning the same project 5 times just to test branches.
```bash
# List all active worktrees
gitauditor worktree list gitauditor

# Create a new isolated folder (sharing the same .git) for a new branch
gitauditor worktree create gitauditor feature/new-screen
```

### 6. Quick Search (Quick Open)
```bash
# Do a fuzzy-search in the catalog and open the project in VS Code (or default editor)
gitauditor catalog open api-gateway
```

---

## 🧱 Modern Architecture (V3)

The tool is based on the most modern pillars of the Python ecosystem:

- `Typer`: Declarative CLI creation.
- `SQLModel`: ORM mixed with Pydantic for the `catalog.db`.
- `Rich`: Spectacular rendering of tables, panels, and Markdown markup in the terminal.
- `Pydantic` + `httpx`: LLM call layer (`AIClient`) that consolidates Structured JSON Requests (Structured Outputs) natively unifying Ollama, OpenAI, and OpenRouter.

---
*GitAuditor - Automate your code governance with intelligence, semantics, and performance.*
