# GitAuditor 🤖

**GitAuditor** evoluiu de um simples script local para um **Catálogo Inteligente de Infraestrutura de Código**. 
Construído em Python com `Typer`, `SQLModel` e `Rich`, ele transforma pastas de repositórios espalhadas pela sua máquina em um banco de dados instantâneo e perfeitamente gerenciável.

Pare de se perguntar *"Onde foi que eu clonei aquele projeto?"* ou *"Quantas vezes eu clonei isso via HTTPS e SSH?"*. O GitAuditor mapeia, cataloga e audita sua infraestrutura automaticamente.

---

## 🌟 O que mudou na Versão 3 (O Catálogo Inteligente)?

O projeto passou por uma metamorfose para se tornar um produto de linha de comando (CLI) profissional:

1. **Banco de Dados Local (`SQLModel` + `SQLite`):** Em vez de escanear o seu disco inteiro a cada inicialização, o GitAuditor agora mantém um catálogo local (`~/.gitauditor/catalog.db`). A interface carrega de forma instantânea.
2. **Metadata Enricher (Deduplicação Lógica):** A nova arquitetura entende URLs remotas. Ele sabe que `git@github.com:owner/repo.git` e `https://github.com/owner/repo.git` são **o mesmo projeto** (Nome Canônico).
3. **Gerenciador de Git Worktrees:** Pare de clonar o mesmo repositório pesado 5 vezes para testar branches diferentes. O GitAuditor cria `worktrees` seguras em pastas vizinhas compartilhando o mesmo histórico do Git.
4. **Dashboard de Saúde:** Detecta repositórios "órfãos" (sem remote) e projetos clonados múltiplas vezes.
5. **Busca Rápida (Quick Open):** Abre rapidamente qualquer repositório no seu editor padrão (`gitauditor catalog open <nome>`).
6. **Empacotamento Moderno:** Migração completa para `pyproject.toml`, CI/CD com GitHub Actions, formatação via `Ruff` e testes unitários.

---

## 🚀 Instalação e Configuração

Com a nova arquitetura de pacotes, instalar o GitAuditor no seu terminal é nativo:

```bash
git clone https://github.com/refernandes/gitauditor.git
cd gitauditor

# Criar e ativar o ambiente virtual (Linux/macOS)
python3 -m venv venv
source venv/bin/activate

# Instalar a aplicação como um pacote global no seu ambiente
pip install -e .
```

A partir de agora, o comando global `gitauditor` estará disponível no seu terminal!

---

## 🛠️ Como Usar (Comandos Principais)

Você pode usar a ferramenta de duas formas: **Menu Interativo (UI)** ou **Comandos Diretos (CLI)**.

### 1. O Menu Interativo
Apenas digite o comando abaixo para abrir a interface em painéis do `Rich`:
```bash
gitauditor
```

### 2. Sincronização do Catálogo (O Primeiro Passo)
Antes de tudo, peça para o GitAuditor mapear sua máquina e preencher o banco de dados:
```bash
gitauditor catalog sync
```

### 3. Dashboard e Limpeza
```bash
# Ver a saúde geral (Órfãos, Duplicados, Total)
gitauditor catalog health

# Exibir um plano de normalização de repositórios duplicados
gitauditor catalog dedupe --plan
```

### 4. Busca e Abertura Rápida
```bash
# Faz um fuzzy-search no catálogo e abre o projeto no VS Code (ou editor padrão)
gitauditor catalog open api-gateway
```

### 5. Git Worktrees (Poupando Disco)
```bash
# Lista todas as worktrees ativas de um projeto
gitauditor worktree list gitauditor

# Cria uma nova pasta isolada compartilhando o mesmo `.git` para uma nova branch
gitauditor worktree create gitauditor feature/nova-tela
```

### 6. IA Amend (A Mágica do Ollama)
Manteve-se o superpoder de Inteligência Artificial: o comando que reescreve todo o seu histórico local validando o `diff` dos commits através do **Ollama** executado na sua máquina:
```bash
gitauditor amend
```

---

## 🧱 Arquitetura Moderna (V3)

- `pyproject.toml`: Configuração de dependências, definindo `gitauditor` como comando principal.
- `src/gitauditor/cli.py`: Controlador principal em **Typer** com menu dinâmico da biblioteca **Rich**.
- `src/gitauditor/commands/`: Subcomandos modulares (`catalog_cmd.py`, `worktree_cmd.py`, etc).
- `src/gitauditor/core/`: Motores de extração. O `catalog.py` lida com o banco SQLite e o `enricher.py` cuida da lógica assíncrona para extrair os *remotes*.
- `.github/workflows/ci.yml`: Pipeline configurado com **Ruff** (Linter/Formatter) e **Pytest**.

---
*GitAuditor - Automatize sua governança de código com inteligência e performance.*
