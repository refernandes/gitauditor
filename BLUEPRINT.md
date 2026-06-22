# GitAuditor Blueprint - V3: O Catálogo Inteligente

Este documento consolida a evolução do **GitAuditor** de um simples scanner de repositórios para um **Catálogo Local Inteligente**. O foco agora não é apenas escanear, mas gerenciar, normalizar e auditar a saúde completa da infraestrutura de código local do usuário.

## 1. Visão Canônica e Metadados Enriquecidos (O "Cérebro")
A base de toda a reestruturação é o abandono do "scan toda hora" para a introdução de um banco de dados local (`SQLite` ou `JSON` persistente).
Cada repositório não será mais apenas um "caminho de pasta", mas uma entidade rica:

- **Host/Owner/Repo** (Ex: `github.com/refernandes/gitauditor`)
- **Tags de Categoria:** `work`, `study`, `archive`, `lab`, `client`
- **Tamanho no Disco** (Megabytes/Gigabytes)
- **Status de Saúde** (Up-to-date, Stale, Broken Remote, Orphans)
- **Última Atividade** (Data do último commit local vs remoto)

Isso desbloqueia consultas ricas e instantâneas:
`gitauditor list --tag work --stale --remote broken`

## 2. Fluxos de Normalização (O "Arrumador")
Ferramentas como o `ghq` provam que caminhos previsíveis salvam vidas.
O GitAuditor será capaz de detectar repositórios espalhados e sugerir uma padronização:
- De: `~/Desktop/projetos-antigos/api`
- Para: `~/Code/github.com/owner/api`

### Comandos-chave propostos:
- `gitauditor repos organize --root ~/Code` (Move e organiza em estrutura canônica)
- `gitauditor repos dedupe --plan` (Mostra quais projetos lógicos estão clonados mais de uma vez)

## 3. Backlog de Implantação Priorizado

### P0 (Missão Crítica)
- **Catálogo Local com Tags/Categorias:** Criação do banco de dados local (`~/.gitauditor.db`) e comandos de sincronização (`gitauditor catalog sync`). Isso transforma o projeto num produto de organização, não apenas num script.
- **Normalização de Paths e Detecção de Duplicatas Lógicas:** O algoritmo que agrupa chaves HTTPS e SSH sob a mesma URL canônica e permite a reorganização sem dor (`--dry-run` para segurança extrema).

### P1 (Valor Imediato)
- **Dashboard de Saúde do Repo:** Detectar remotes quebrados, diretórios `.git` inflados que precisam de um `git gc`, e repositórios abandonados ("stale").
- **Cleanup Seguro com Preview:** Interface para deleção ou arquivamento em massa de repositórios podres ou órfãos, sempre mostrando o ganho de disco.
- **Busca Rápida e Abertura:** Achar repos e abri-los direto no editor padrão (`gitauditor open <repo_alias>`).

### P2 (Funcionalidades Avançadas de Fluxo)
- **Worktree Manager:** Em vez de clonar de novo para testar a branch X, sugerir e criar `git worktrees` (`gitauditor worktree create repo-x feature/teste`). Isso poupa muito espaço de HD e mantém as coisas higienizadas.
- **Templates e Bootstrap:** Ajudar na padronização de novos projetos locais.
- **Suporte a Sparse-Checkout:** Para monorepos que destroem a máquina local, facilitando a vida para baixar só as peças necessárias.

## 4. Arquitetura de Comandos (Typer)

A fundação recém construída com o **Typer** permite fatiarmos o CLI de maneira muito elegante. O blueprint de comandos será:

```bash
# Sincroniza e populo o banco de dados
gitauditor catalog sync

# Relatórios rápidos e filtragem
gitauditor repos list --tag work --stale
gitauditor catalog health

# Ações de Limpeza e Organização
gitauditor catalog dedupe --plan
gitauditor repos organize --root ~/Code --dry-run
gitauditor repos prune

# Agilidade e Fluxo
gitauditor catalog open backend-api
gitauditor worktree create api feature/teste
```

## 5. Backlog Futuro: Phase 3 (Semantic AI Layer)

A próxima grande evolução do GitAuditor foca em integrar Inteligência Artificial (LLMs Locais via Ollama ou APIs Externas plugáveis) não apenas como geradores de mensagens, mas como uma **Camada Semântica Confiável** sobre o inventário Git.

### Princípios de Design e Governança
Para que a IA adicione valor real sem transformar o produto em uma caixa de surpresas, as seguintes regras guiarão a arquitetura P3:

1. **Multi-Provider API:** A camada de LLM deve ser agnóstica, permitindo o uso do Ollama local por padrão, mas com portas abertas para provedores externos via chaves de API.
2. **Governança no Catálogo:** O banco de dados (`Repo`) não guardará apenas as respostas. Ele rastreará a proveniência: `ai_model`, `ai_prompt_version`, `ai_updated_at`, `ai_confidence`, `ai_error` e `ai_source_hash`.
3. **Estratégia de Cache e Hash:** A IA só será chamada se o contexto base do repositório mudar. Se o hash do README + manifestos + árvore for o mesmo, lemos do banco.
4. **Validação Estruturada (Pydantic) + Retry:** As saídas da IA deverão seguir schemas JSON estritos e separados por feature, com lógica de retry caso a estrutura venha inválida.
5. **Heurística Antes da IA (Fallback Determinístico):** A classificação (`tag`) começará sempre por regras rígidas e determinísticas (ex: detectar `package.json`). O LLM entra como enriquecedor. Se o LLM falhar, a heurística garante a funcionalidade.
6. **Limites do LLM:** No *repo review*, a IA não substituirá scanners de segurança (como gitleaks). Ela focará em smells qualitativos, arquitetura e dicas humanas.
7. **Contexto Hierárquico Inteligente:** O extrator não vai só cuspir a pasta inteira para o LLM. Ele enviará metadados do Git, a árvore resumida por profundidade, o README truncado, manifestos chaves (`pyproject.toml`, `package.json`, etc) e excluirá arquivos nocivos (`.venv`, `node_modules`).

### Roadmap Fatiado da Fase P3

Para evitar complexidade monstruosa, a implementação será feita em 4 entregas atômicas:

- **P3.1 | Summarize & Foundation:**
  - Adição dos campos semânticos e de governança no banco SQLite.
  - Implementação do "Extrator de Contexto" hierárquico com cálculo de Hash.
  - Implementação do motor Multi-Provider de IA com Structured Outputs (JSON) usando Pydantic.
  - Comando: `gitauditor catalog summarize`.

- **P3.2 | Auto-Tagging Híbrido:**
  - Comando: `gitauditor catalog tag --auto`.
  - Inferência primeiro determinística, depois refinada pela IA para categorizar projetos (`work`, `api`, `lab`, `archive`).

- **P3.3 | Local Review (Code Quality):**
  - Comando: `gitauditor repo review`.
  - Foco restrito em analisar diffs curtos ou *staged* para apontar falhas qualitativas de design antes do commit.

- **P3.4 | Rascunho de Documentação:**
  - Comando: `gitauditor repo readme-draft`.
  - Geração estruturada de READMEs a partir da stack detectada para reativar repositórios "mortos".

---
*Status: P0, P1, P2 Concluídos na Versão 3. Fase P3 em estágio de arquitetura e aprovação.*
