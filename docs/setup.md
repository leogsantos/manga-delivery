# Configuração do ambiente local

## Sumário

- [Pré-requisitos](#pré-requisitos)
- [Clone do repositório](#clone-do-repositório)
- [Instalação de dependências](#instalação-de-dependências)
- [Configuração do Google OAuth2](#configuração-do-google-oauth2)
- [Configuração do `.env`](#configuração-do-env)
- [Rodando localmente](#rodando-localmente)
- [Catálogo de mangás disponíveis](#catálogo-de-mangás-disponíveis)
- [Testes](#testes)
- [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

- **Python 3.13+** — verifique com `python --version`
- **[uv](https://github.com/astral-sh/uv)** — gerenciador de dependências e ambientes virtuais
- **Git**
- Conta Google (para Google Drive e Gmail)

### Instalando o uv

No Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

No Linux/macOS:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Após instalar, reinicie o terminal e confirme:
```bash
uv --version
```

> **⚠️ Atenção (Windows):** Se o comando `uv` não for reconhecido após instalar, adicione `%USERPROFILE%\.local\bin` ao PATH do sistema. Vá em Variáveis de Ambiente → PATH → Novo.

---

## Clone do repositório

```bash
git clone https://github.com/leogssantos/manga-delivery.git
cd manga-delivery
```

---

## Instalação de dependências

```bash
uv sync
uv run playwright install chromium
```

O `uv sync` cria o `.venv` e instala todas as dependências do `pyproject.toml`. O segundo comando baixa o binário do Chromium usado pelo Playwright.

> **💡 Dica:** O `uv sync` sem flags instala as dependências de produção. Para incluir as de desenvolvimento (pytest, ruff), já estão configuradas no `[dependency-groups]` do `pyproject.toml` e são instaladas automaticamente no ambiente local.

> **⚠️ Atenção (Windows + Kaspersky):** O Kaspersky pode bloquear o download do Chromium pelo Playwright. Se o `playwright install chromium` travar ou falhar com erro de conexão, desabilite temporariamente a proteção de rede do Kaspersky durante o download.

---

## Configuração do Google OAuth2

Antes de rodar o pipeline, você precisa de um projeto no Google Cloud com as APIs configuradas e um `token.json` gerado localmente.

Veja o guia completo em [docs/google-auth.md](google-auth.md).

Resumo dos arquivos necessários:
- `secrets/oauth_client.json` — baixado do Google Cloud Console
- `secrets/token.json` — gerado ao rodar `authenticate.py`

---

## Configuração do `.env`

Copie o arquivo de exemplo e preencha:

```bash
cp .env.example .env
```

Conteúdo do `.env`:

```env
GDRIVE_OAUTH_CLIENT_FILE=secrets/oauth_client.json
GDRIVE_TOKEN_FILE=secrets/token.json
GDRIVE_FOLDER_ID=seu_folder_id_aqui
MANGA_SLUG=one-piece
GMAIL_FROM=seu@gmail.com
GMAIL_TO=destino1@email.com,destino2@email.com
```

### Descrição das variáveis

| Variável | Descrição |
|---|---|
| `GDRIVE_OAUTH_CLIENT_FILE` | Path para o `oauth_client.json` baixado do Google Cloud Console |
| `GDRIVE_TOKEN_FILE` | Path para o `token.json` gerado pelo `authenticate.py` |
| `GDRIVE_FOLDER_ID` | ID da pasta no Google Drive onde os arquivos serão salvos |
| `MANGA_SLUG` | Slug do mangá (ex: `one-piece`, `bleach`, `chainsaw-man-pt-br`) |
| `GMAIL_FROM` | Email do remetente (deve ser o mesmo email autenticado) |
| `GMAIL_TO` | Emails destinatários separados por vírgula |

### Como obter o `GDRIVE_FOLDER_ID`

1. Acesse [drive.google.com](https://drive.google.com) e crie uma pasta chamada `manga-delivery`
2. Abra a pasta e copie o ID da URL:
   ```
   https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUv
                                           ^^^^^^^^^^^^^^^^^^^^^^^^
                                           esse é o GDRIVE_FOLDER_ID
   ```

---

## Rodando localmente

Com o `.env` configurado e o `token.json` gerado:

```bash
uv run python -m src.main
```

O pipeline vai:
1. Verificar se há capítulo novo para o slug configurado
2. Baixar as imagens se houver novidade
3. Converter para PDF e EPUB
4. Fazer upload no Google Drive
5. Enviar email
6. Atualizar o estado

Se não houver capítulo novo, o pipeline encerra com a mensagem:
```
Nenhum capítulo novo. Encerrando.
```

---

## Catálogo de mangás disponíveis

Para ver todos os títulos disponíveis no site com seus slugs:

```bash
uv run python -m src.catalog
```

Saída esperada:
```
SLUG                                               ÚLTIMO UPDATE
----------------------------------------------------------------------
one-piece                                          2025-06-01
bleach                                             2025-05-28
chainsaw-man-pt-br                                 2025-05-25
...

Total: 847 títulos
```

---

## Testes

### Testes unitários (sem I/O externo)

```bash
uv run pytest tests/unit/
```

### Testes de integração (chamam APIs reais)

> **⚠️ Atenção:** Os testes de integração fazem requisições reais ao mangalivre.to. Requerem conexão com a internet e podem ser lentos.

```bash
uv run pytest tests/integration/ -m integration
```

### Todos os testes exceto integração

```bash
uv run pytest -m "not integration"
```

### Com output detalhado

```bash
uv run pytest -v
```

---

## Troubleshooting

### `uv` não encontrado após instalar (Windows)

Adicione `%USERPROFILE%\.local\bin` ao PATH do sistema:

1. Pesquise "Variáveis de ambiente" no menu Iniciar
2. Em "Variáveis do sistema", selecione `Path` → Editar
3. Adicione: `C:\Users\SEU_USUARIO\.local\bin`
4. Reinicie o terminal

### Playwright trava ou falha no download (Windows + Kaspersky)

O Kaspersky bloqueia conexões do instalador do Playwright. Desabilite temporariamente:

1. Abra o Kaspersky
2. Vá em Proteção → Proteção de rede → Pause temporariamente
3. Rode `uv run playwright install chromium`
4. Reative a proteção

### Erro `418 I'm a Teapot` ao rodar o pipeline

O site bloqueou a requisição por User-Agent inválido. Verifique `BROWSER_HEADERS` em `src/utils.py` e atualize o User-Agent para uma versão recente do Chrome.

### `ModuleNotFoundError: No module named 'src'`

Rode sempre com `uv run python -m src.main` (não `python src/main.py`). O `uv run` configura o `PYTHONPATH` corretamente.

### `Token OAuth2 não encontrado`

Execute `uv run python authenticate.py` para gerar o `secrets/token.json`. Veja [docs/google-auth.md](google-auth.md).

### `GDRIVE_FOLDER_ID não definida`

Verifique se o `.env` foi criado (`cp .env.example .env`) e se o `GDRIVE_FOLDER_ID` está preenchido.
