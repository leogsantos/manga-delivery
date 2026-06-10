# Contribuindo com o manga-delivery

Obrigado pelo interesse em contribuir! Este documento explica como funciona o processo.

## Sumário

- [Antes de começar](#antes-de-começar)
- [Fluxo de contribuição](#fluxo-de-contribuição)
- [Adicionando suporte a um novo site de scan](#adicionando-suporte-a-um-novo-site-de-scan)
- [Padrões do projeto](#padrões-do-projeto)
- [Reportando bugs](#reportando-bugs)
- [Sugerindo funcionalidades](#sugerindo-funcionalidades)

---

## Antes de começar

- Verifique se já existe uma [issue](https://github.com/leogssantos/manga-delivery/issues) aberta para o que você quer fazer
- Para mudanças grandes, abra uma issue primeiro para discutir antes de implementar
- Para correções pequenas (typo, bug simples), pode abrir o PR direto

---

## Fluxo de contribuição

```
fork → clone → branch feature/* ou fix/* → PR para develop → review → merge
```

### 1. Fork e clone

```bash
git clone https://github.com/SEU_USUARIO/manga-delivery.git
cd manga-delivery
```

### 2. Instala o ambiente

```bash
uv sync
uv run playwright install chromium
```

### 3. Cria um branch

```bash
# nova funcionalidade
git checkout -b feature/nome-da-feature

# correção de bug
git checkout -b fix/nome-do-bug
```

### 4. Implementa e testa

Antes de abrir o PR, garanta que os testes unitários passam:

```bash
uv run pytest tests/unit/
```

Se fizer mudanças que afetam o comportamento do pipeline, teste localmente também:

```bash
cp .env.example .env
# preencha o .env com suas credenciais
uv run python -m src.main
```

### 5. Abre o Pull Request

- PR sempre para o branch `develop`, nunca direto para `main`
- Preencha a descrição com o que foi feito e como testar
- Aguarde review

---

## Adicionando suporte a um novo site de scan

O projeto foi pensado para ser extensível. Para adicionar suporte a um novo site:

1. Crie `src/scraper_{nome_do_site}.py` seguindo a interface do `scraper.py`:
   - `download_chapter(slug, chapter_url) -> list[Path]`
   - `cleanup_chapter(slug, chapter_url) -> None`

2. Crie `src/checker_{nome_do_site}.py` seguindo a interface do `checker.py`:
   - `get_latest_chapter(slug) -> dict | None`

3. Documente o novo site no README na seção de sites suportados

4. Abra o PR com exemplos de slugs válidos para teste

---

## Padrões do projeto

### Python

- Versão mínima: **3.13**
- Gerenciamento de dependências: **uv** (`pyproject.toml`)
- Linting: **ruff** (`uv run ruff check src/`)

### Código

- Exceptions customizadas para todos os erros de domínio (herdam de `MangaDeliveryError`)
- Retry exponencial via decorator `@retry` para chamadas HTTP instáveis
- Funções públicas com docstring
- Logs via `logging` — sem `print()` em produção
- Retorna estruturas vazias em vez de re-raise quando o erro for recuperável

### Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: adiciona suporte ao site xyz
fix: corrige parsing de capítulos com número decimal
docs: atualiza setup.md com troubleshooting do Kaspersky
refactor: extrai lógica de autenticação para módulo próprio
chore: atualiza dependências
```

### Branches

| Prefixo | Uso |
|---|---|
| `feature/` | novas funcionalidades |
| `fix/` | correções de bug |
| `docs/` | apenas documentação |
| `refactor/` | refatoração sem mudança de comportamento |

---

## Reportando bugs

Abra uma issue com:

- Descrição clara do problema
- Passos para reproduzir
- Output completo do erro (logs)
- Versão do Python e sistema operacional
- Slug do mangá que estava sendo processado

---

## Sugerindo funcionalidades

Abra uma issue com a label `enhancement` descrevendo:

- O problema que a feature resolve
- Como você imagina que deveria funcionar
- Alternativas que considerou

---

Dúvidas? Abre uma issue com a label `question`.
