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
gitauditor repos health

# Ações de Limpeza e Organização
gitauditor repos dedupe --plan
gitauditor repos organize --root ~/Code --dry-run
gitauditor repos prune

# Agilidade e Fluxo
gitauditor open backend-api
gitauditor worktree create api feature/teste
```

---
*Status: Aprovado para início do desenvolvimento P0.*
