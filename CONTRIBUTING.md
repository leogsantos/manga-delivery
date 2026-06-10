# Contribuindo com o manga-delivery

Obrigado pelo interesse em contribuir! Este documento explica como funciona o processo de contribuição.

---

## Antes de começar

- Verifique se já existe uma [issue](https://github.com/leogssantos/manga-delivery/issues) aberta para o que você quer fazer
- Para mudanças grandes, abra uma issue primeiro para discutir antes de implementar
- Para correções pequenas (typo, bug simples), pode abrir o PR direto

---

## Fluxo de contribuição

```
fork → clone → feature/* ou fix/* → PR para develop → review → merge
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

Antes de abrir o PR, garante que o pipeline roda localmente:

```bash
cp .env.example .env
# preenche o .env com suas credenciais de teste
uv run python -m src.main
```

### 5. Abre o Pull Request

- PR sempre para o branch `develop`, nunca direto para `main`
- Preenche o template do PR com o que foi feito e como testar
- Aguarda review

---

## Adicionando suporte a um novo site de scan

O projeto foi pensado para ser extensível. Para adicionar suporte a um novo site:

1. Cria `src/scraper_{nome_do_site}.py` seguindo a mesma interface do `scraper.py`:
   - Função `download_chapter(slug, chapter_url) -> list[Path]`
   - Função `cleanup_chapter(slug, chapter_url) -> None`

2. Cria `src/checker_{nome_do_site}.py` seguindo a interface do `checker.py`:
   - Função `get_latest_chapter(slug) -> dict | None`

3. Documenta o novo site no README na seção de sites suportados

4. Abre o PR com exemplos de slugs válidos para teste

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
docs: atualiza README com novo slug
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

Abre uma issue com:

- Descrição clara do problema
- Passos para reproduzir
- Output do erro (logs completos)
- Versão do Python e sistema operacional
- Slug do mangá que estava sendo processado

---

## Sugerindo funcionalidades

Abre uma issue com a label `enhancement` descrevendo:

- O problema que a feature resolve
- Como você imagina que deveria funcionar
- Alternativas que considerou

---

## Dúvidas

Abre uma issue com a label `question` — respondemos por lá.
