# GitAuditor 🛡️🤖

GitAuditor é uma ferramenta de **linha de comando (CLI)** construída em Python (utilizando a biblioteca `Rich`) focada em gerenciar, auditar e organizar repositórios Git na sua máquina local. Ele centraliza a visualização dos seus repositórios, avalia permissões SSH, encontra repositórios duplicados e integra-se nativamente com Inteligência Artificial (**Ollama**) para reescrever o histórico de commits de forma totalmente automatizada.

## Funcionalidades Principais

1. 🔍 **Auditoria Global Assíncrona:** Busca rapidamente por diretórios e repositórios Git ocultos em toda a sua máquina e avalia o status das conexões remotas via comandos assíncronos não-bloqueantes.
2. 🧹 **Varredura de Duplicatas e Branches:** Encontra repositórios clonados múltiplas vezes, independente de estarem usando HTTPS ou SSH, facilitando a limpeza do seu disco.
3. 🤖 **AI Commit Amend (Ollama):** Reescreva todo o seu histórico local! A IA avalia os `diffs` dos commits antigos e reescreve as mensagens (Rebase Interativo) baseando-se nas melhores práticas. Inclui suporte a pagição, lotes sequenciais (Batch Processing) e proteção nativa da árvore de merges.
4. 🔑 **Gerenciador de Identidades SSH:** Analisa sua pasta `~/.ssh`, lista as criptografias ativas e realiza testes de autenticação reais com os servidores do GitHub/GitLab.

## Pré-requisitos

1. **Python 3.10+** e **Git** instalado.
2. **Ollama:** Para usar a IA local, tenha o Ollama rodando (ex: `http://localhost:11434/`).
   - O projeto utiliza por padrão o modelo `llama3`, mas você pode configurá-lo alterando no `src/core/ollama_api.py`.

## Instalação e Execução

Clone o repositório e crie um ambiente virtual:

```bash
git clone https://github.com/refernandes/gitauditor.git
cd gitauditor

# Criar e ativar o ambiente virtual (Linux/macOS)
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar a aplicação
python -m src
```

## Arquitetura do Projeto (V2)

A arquitetura do GitAuditor evoluiu de uma TUI monolítica para um CLI Modular (Clean Architecture):

- `src/__main__.py`: Entrypoint e orquestrador.
- `src/cli.py`: Controlador principal do CLI, renderização de tabelas e painéis `Rich`.
- `src/commands/`: Comandos encapsulados (Audit, Repo, Amend, SSH).
- `src/core/`: Motores core (GitPython + Subprocess Async, Scanner Async, Ollama Caching via SHA-256).
- `tests/`: Bateria de testes isolados validando operações de Rebase, Push Async e Parsing.

## Segurança

O sistema foi rigorosamente auditado para evitar vulnerabilidades de Code Injection durante a criação de scripts de editor (`GIT_EDITOR`), e utiliza Sandboxing e Fallbacks multiplataforma para garantir estabilidade em Linux, macOS e Windows.

---
*Automatize sua gestão de versionamento com Inteligência e Precisão.*
