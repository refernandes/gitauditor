# GitAuditor 🤖

**GitAuditor** evoluiu de um simples script local para um **Catálogo Inteligente de Infraestrutura de Código turbinado por Inteligência Artificial**.
Construído em Python com `Typer`, `SQLModel` e `Rich`, ele transforma pastas de repositórios espalhadas pela sua máquina em um banco de dados local perfeitamente gerenciável, ao mesmo tempo que entende o contexto semântico do seu código usando provedores de IA como OpenAI, OpenRouter ou Ollama local.

Pare de se perguntar *"Onde foi que eu clonei aquele projeto?"*, *"Sobre o que é este repositório legado?"* ou *"Como escrevo notas de release para estes últimos 30 commits?"*. O GitAuditor mapeia, cataloga, audita e analisa sua infraestrutura automaticamente.

---

## 🌟 O que mudou na Versão 3 (O Catálogo Semântico)?

O projeto passou por uma metamorfose impressionante, implementando o **Blueprint P3 (Camada Semântica)** para ser o seu co-piloto de governança:

1. **Banco de Dados Local e Eficiente (`SQLModel` + `SQLite`):** Mantém um catálogo local (`~/.gitauditor/catalog.db`), carregando instantaneamente e deduplicando projetos clonados.
2. **Gerenciador de Git Worktrees (P2):** Cria `worktrees` seguras em pastas vizinhas compartilhando o mesmo histórico do Git, poupando espaço no disco.
3. **Painel de Configuração de IA (Multi-Provedor):** Suporte total a **Ollama** (Local/Gratuito), **OpenAI** (Nuvem/Alta Precisão) e **OpenRouter** (Multi-modelos).
4. **Extração de Contexto Semântico:** Usa hashes para analisar a árvore do projeto e o README sem gastar CPU, gerando resumos (Sumário, Stack Tecnológica, Nível de Atividade) usando LLMs.
5. **Classificação Automática (Auto-Tagging):** Um sistema de dupla verificação. Primeiro escaneia arquivos chaves (heurística determinística) e depois usa IA para refinar e criar tags de negócio (`api`, `frontend`, `monorepo`, etc).
6. **Code Review Local:** Um revisor estrito que analisa o seu *diff* atual no repositório antes do commit, focando em code smells, arquitetura e riscos.
7. **Gerador de Changelogs:** Varre o histórico de commits (com limite personalizável) e usa IA para gerar um *Release Notes* humano e estruturado separando Bugs, Features e Refactors.

---

## 🚀 Instalação e Configuração

A instalação do GitAuditor como pacote CLI é nativa:

```bash
git clone https://github.com/refernandes/gitauditor.git
cd gitauditor

# Criar e ativar o ambiente virtual (Linux/macOS)
python3 -m venv venv
source venv/bin/activate

# Instalar a aplicação como um pacote interativo
pip install -e .
```

A partir de agora, o comando global `gitauditor` estará disponível no seu terminal!

---

## 🖥️ A Interface Visual (O Modo Interativo)

Ao digitar apenas `gitauditor` no terminal, você acessa a interface interativa (UI) construída com `Rich`. Essa interface apresenta uma tabela central com todos os seus repositórios e um menu de ações inferior.

Na **Versão 3**, foi adicionado o Submenu de Inteligência Artificial para que você possa rodar qualquer ferramenta sem precisar decorar comandos de terminal:

```text
[bold yellow]Menu Principal:[/bold yellow]
[1] 🔍 Ver Detalhes de um Repositório
[2] 📂 Buscar e Abrir no Editor (Open)
[3] 📊 Dashboard de Saúde do Catálogo
[4] 🧹 Resolver Repositórios Duplicados
[5] 🌳 Gerenciar Git Worktrees
[6] 🤖 Ferramentas de Inteligência Artificial (V3)
[7] 🔑 Gerenciar Chaves e Identidades SSH
[8] 🔄 Sincronizar Catálogo Local
[9] 🏷️ Filtrar Tabela
[0] 🚪 Sair
```

Ao escolher a **Opção 6**, você terá acesso a todo o poder Semântico em cima da tabela visual (o sistema te pedirá o ID do repositório antes de rodar a IA):
- `[1] IA Amend`
- `[2] IA Code Review`
- `[3] IA Changelog`
- `[4] IA Configuração (Mudar Provedor)`
- `[5] IA Auto-Tagging`
- `[6] IA Summarize`

---

## 🛠️ O Modo Automação (CLI Commands)

Se você prefere scripts ou comandos diretos, todas as opções da UI também funcionam via subcomandos CLI.

### 1. Configurando sua Inteligência Artificial
Você pode escolher qual motor cognitivo o GitAuditor vai usar (Ollama para rodar 100% offline, OpenAI ou OpenRouter para modelos avançados em nuvem).
```bash
gitauditor config
```

### 2. Sincronização e Saúde do Catálogo
Antes de explorar os superpoderes, popule o banco de dados da sua máquina:
```bash
# Mapeia sua máquina
gitauditor catalog sync

# Ver a saúde geral (Órfãos, Duplicados, Total)
gitauditor catalog health

# Exibir um plano de normalização de repositórios duplicados
gitauditor catalog dedupe --plan
```

### 3. A Camada Semântica de IA (V3)
Os novos comandos poderosos acionam a inteligência para interagir com o seu código:

```bash
# Resume o repositório, identifica a tech stack e analisa riscos/atividade baseando-se na árvore e manifestos
gitauditor catalog summarize

# Auto-classifica o repositório atual combinando heurísticas locais de arquivos com análise de IA
gitauditor catalog tag-auto

# Realiza um "Local Code Review" no diff atual não commitado (code smells e arquitetura)
gitauditor review

# Gera um Changelog profissional dos commits passados (Padrão: Todos, ou limite)
gitauditor changelog --limit 15
```

### 4. IA Amend (A Mágica da Reescrita de Histórico)
Reescreve o seu histórico local de commits valendo-se do seu diff para gerar novas mensagens no padrão *Conventional Commits*:
```bash
gitauditor amend
```

### 5. Git Worktrees (Poupando Disco)
Pare de fazer 5 clones do mesmo projeto só para testar branches.
```bash
# Lista todas as worktrees ativas
gitauditor worktree list gitauditor

# Cria uma nova pasta isolada (compartilhando o mesmo .git) para uma nova branch
gitauditor worktree create gitauditor feature/nova-tela
```

### 6. Busca Rápida (Quick Open)
```bash
# Faz um fuzzy-search no catálogo e abre o projeto no VS Code (ou editor padrão)
gitauditor catalog open api-gateway
```

---

## 🧱 Arquitetura Moderna (V3)

A ferramenta é baseada nos pilares mais modernos do ecossistema Python:

- `Typer`: Criação declarativa da CLI.
- `SQLModel`: ORM misturado com Pydantic para o `catalog.db`.
- `Rich`: Renderização espetacular de tabelas, painéis e marcações Markdown no terminal.
- `Pydantic` + `httpx`: Camada de chamadas LLM (`AIClient`) que consolida requests JSON Estruturadas (Structured Outputs) unificando Ollama, OpenAI e OpenRouter nativamente.

---
*GitAuditor - Automatize sua governança de código com inteligência, semântica e performance.*
