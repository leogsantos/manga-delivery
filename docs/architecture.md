# Arquitetura do manga-delivery

## Sumário

- [Visão geral](#visão-geral)
- [Fluxo do pipeline](#fluxo-do-pipeline)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Módulos](#módulos)
  - [main.py](#mainpy)
  - [checker.py](#checkerpy)
  - [scraper.py](#scraperpy)
  - [converter/](#converter)
  - [state.py](#statepy)
  - [storage/gdrive.py](#storagegdrivepy)
  - [notifier/email.py](#notifieremailpy)
  - [catalog.py](#catalogpy)
  - [exceptions.py e utils.py](#exceptionspy-e-utilspy)
- [Decisões técnicas](#decisões-técnicas)
- [Fluxo de branches](#fluxo-de-branches)

---

## Visão geral

O manga-delivery é um pipeline RPA executado via GitHub Actions que:

1. Detecta capítulos novos de um mangá no site [mangalivre.to](https://mangalivre.to)
2. Renderiza a página com Playwright e baixa as imagens em paralelo
3. Converte as imagens para PDF e EPUB
4. Faz upload dos arquivos no Google Drive
5. Envia o EPUB por email via Gmail API
6. Atualiza o estado do pipeline no próprio Drive

Toda a orquestração é feita por `src/main.py`. Cada etapa tem seu próprio módulo com responsabilidade isolada.

---

## Fluxo do pipeline

```
GitHub Actions (cron: 0 12 * * *)
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│  checker.py                                               │
│  1. GET https://mangalivre.to/manga/{slug}/               │
│     └── extrai manga_id e nonce embutidos no HTML         │
│  2. POST .../ajax/chapters/ (Madara AJAX API)             │
│     └── retorna lista de capítulos em HTML                │
│  3. Compara chapters[0].url com state.last_chapter        │
│     └── se igual → encerra (sem novidade)                 │
└──────────────────────────┬────────────────────────────────┘
                           │ capítulo novo detectado
                           ▼
┌───────────────────────────────────────────────────────────┐
│  scraper.py                                               │
│  1. Playwright renderiza a página do capítulo (headless)  │
│     └── aguarda networkidle para garantir lazy-load       │
│  2. BeautifulSoup extrai src das img.wp-manga-chapter-img │
│  3. Download paralelo das imagens (semáforo: 5 threads)   │
│     └── salva em downloads/{slug}/capitulo-{N}/          │
└──────────────────────────┬────────────────────────────────┘
                           │ list[Path] das imagens
                           ▼
┌───────────────────────────────────────────────────────────┐
│  converter/                                               │
│  to_pdf.py:  webp → jpeg (Pillow) → PDF (img2pdf)        │
│  to_epub.py: webp → jpeg (Pillow) → EPUB (EbookLib)      │
│  └── ambos salvam em output/{slug}/                       │
└──────────────────────────┬────────────────────────────────┘
                           │ pdf_path, epub_path
                           ▼
┌───────────────────────────────────────────────────────────┐
│  storage/gdrive.py                                        │
│  1. Autentica com token OAuth2 (renova automaticamente)   │
│  2. Cria subpasta {slug}/ dentro de GDRIVE_FOLDER_ID      │
│  3. Upload do PDF e do EPUB                               │
│  └── retorna webViewLink dos arquivos                     │
└──────────────────────────┬────────────────────────────────┘
                           │ drive_link_epub
                           ▼
┌───────────────────────────────────────────────────────────┐
│  notifier/email.py                                        │
│  1. Constrói MIMEMultipart com EPUB anexado               │
│  2. Envia via Gmail API (users.messages.send)             │
│  └── destinatários definidos em GMAIL_TO                  │
└──────────────────────────┬────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────┐
│  scraper.cleanup_chapter()                                │
│  └── deleta downloads/{slug}/capitulo-{N}/               │
│                                                           │
│  state.save_state()                                       │
│  └── grava state.json no Drive:                          │
│      .manga-delivery-state/{slug}/state.json             │
│      { last_chapter: url, last_run: ISO timestamp }      │
└───────────────────────────────────────────────────────────┘
```

---

## Estrutura de pastas

```
manga-delivery/
├── .github/
│   └── workflows/
│       ├── pipeline.yml        # cron diário + workflow_dispatch
│       ├── build-image.yml     # build e push da imagem para o GHCR
│       └── tests.yml           # roda testes unitários em todo PR
├── src/
│   ├── main.py                 # orquestrador do pipeline
│   ├── checker.py              # detecta capítulo novo (Madara AJAX API)
│   ├── scraper.py              # download das imagens via Playwright
│   ├── state.py                # lê/escreve state.json no Google Drive
│   ├── catalog.py              # lista mangás via sitemap XML
│   ├── exceptions.py           # hierarquia de exceptions customizadas
│   ├── utils.py                # retry decorator e browser headers
│   ├── converter/
│   │   ├── __init__.py         # conversão webp → jpeg compartilhada
│   │   ├── to_pdf.py           # imagens → PDF via img2pdf
│   │   └── to_epub.py          # imagens → EPUB via EbookLib
│   ├── storage/
│   │   └── gdrive.py           # upload para o Google Drive
│   └── notifier/
│       └── email.py            # envio de email via Gmail API
├── tests/
│   ├── unit/                   # testes com mocks, sem I/O externo
│   └── integration/            # testes que chamam APIs reais (marcados @integration)
├── secrets/                    # credenciais locais (gitignored)
│   ├── oauth_client.json
│   └── token.json
├── output/                     # PDFs e EPUBs gerados (gitignored)
├── downloads/                  # imagens temporárias (gitignored)
├── authenticate.py             # gera token.json via OAuth2 (roda uma vez)
├── Dockerfile                  # imagem baseada em mcr.microsoft.com/playwright/python
├── docker-compose.yaml
├── pyproject.toml
├── .env.example
└── .python-version             # 3.13
```

---

## Módulos

### main.py

Ponto de entrada do pipeline. Chama cada módulo em sequência, sem lógica de domínio própria. É a cola entre os módulos.

```python
uv run python -m src.main
```

### checker.py

Detecta se há um capítulo novo sem usar Playwright — só `httpx` estático.

Fluxo interno:
1. `_fetch_page(slug)` — GET na página do mangá, extrai o HTML
2. `_extract_page_meta(slug)` — regex para extrair `manga_id` e `nonce` embutidos no HTML
3. `_fetch_chapters(slug, manga_id, nonce)` — POST na rota AJAX do Madara WordPress plugin, recebe HTML com a lista de capítulos
4. `get_latest_chapter(slug)` — compara `chapters[0].url` com `state.last_chapter` carregado do Drive

O `nonce` é um token de segurança do WordPress gerado a cada page load. Sem ele, a AJAX API retorna erro.

### scraper.py

Responsável por renderizar a página do capítulo e baixar as imagens.

- Usa Playwright `sync_api` com Chromium headless
- Aguarda `networkidle` para garantir que imagens com lazy-load sejam carregadas
- Extrai URLs das imagens pela classe CSS `wp-manga-chapter-img`
- Download paralelo com `asyncio` + `httpx.AsyncClient`, limitado por semáforo de 5 conexões
- Nomeia os arquivos sequencialmente com zero-padding (`001.webp`, `002.webp`, ...)
- `cleanup_chapter()` deleta a pasta de imagens após conversão

### converter/

`__init__.py` expõe `convert_image_to_jpeg(path) -> bytes` — conversão comum para ambos os formatos (webp não é suportado diretamente por img2pdf e EbookLib).

`to_pdf.py`:
- Converte cada imagem para JPEG via Pillow
- Usa `img2pdf.convert()` para montar o PDF preservando a qualidade original
- Salva em `output/{slug}/{slug}-capitulo-{N}.pdf`

`to_epub.py`:
- Cria estrutura EPUB 3 via EbookLib
- Cada imagem vira um item de imagem + um documento HTML no spine
- Salva em `output/{slug}/{slug}-capitulo-{N}.epub`

### state.py

Gerencia persistência do estado do pipeline no Google Drive, na pasta `.manga-delivery-state/{slug}/state.json`.

Estrutura do `state.json`:
```json
{
  "last_chapter": "https://mangalivre.to/manga/one-piece/capitulo-1183/",
  "last_run": "2025-06-01T12:03:45+00:00"
}
```

- `load_state(slug)` — baixa o arquivo do Drive via `MediaIoBaseDownload`; retorna `DEFAULT_STATE` em caso de falha (pipeline não trava)
- `save_state(slug, chapter_url)` — faz update se o arquivo já existe, cria se não existe
- A pasta `.manga-delivery-state/` fica separada dos arquivos de consumo (PDF/EPUB) dentro da mesma pasta raiz no Drive

### storage/gdrive.py

Upload de arquivos para o Google Drive.

- Autentica via `Credentials.from_authorized_user_file` e renova o token automaticamente se expirado
- Cria a subpasta `{slug}/` dentro de `GDRIVE_FOLDER_ID` se não existir
- Upload via `MediaFileUpload` com `resumable=True`
- Retorna `webViewLink` do arquivo criado

### notifier/email.py

Envia o EPUB por email via Gmail API.

- Constrói `MIMEMultipart` com corpo HTML e o EPUB como `MIMEApplication`
- Usa `users.messages.send` com payload base64url-encoded
- `GMAIL_TO` aceita múltiplos destinatários separados por vírgula

### catalog.py

Lista todos os mangás disponíveis no site via sitemap XML.

```bash
uv run python -m src.catalog
```

Faz GET em `https://mangalivre.to/wp-manga-sitemap.xml`, extrai `<loc>` de cada entrada e formata slug + data de última atualização. Útil para descobrir slugs válidos.

### exceptions.py e utils.py

`exceptions.py` define a hierarquia de exceptions do domínio:
- `MangaDeliveryError` — base
- `BotBlockedError`, `PageFetchError`, `NonceMissingError`, `ChapterFetchError`, `ChapterParseError`

`utils.py` contém:
- `BROWSER_HEADERS` — User-Agent e headers HTTP que imitam um browser real, necessários para evitar bloqueio 418
- `@retry(max_attempts, base_delay, exceptions)` — decorator de retry com backoff exponencial para chamadas HTTP instáveis

---

## Decisões técnicas

### Por que Playwright em vez de httpx estático no scraper?

As páginas de capítulo no mangalivre.to são renderizadas dinamicamente com JavaScript. As imagens usam lazy-load e só aparecem no DOM após a execução de scripts. Uma requisição `httpx` estática retorna HTML sem as URLs das imagens. O Playwright renderiza a página completa e aguarda `networkidle`, garantindo que todas as imagens estejam no DOM antes da extração.

O `checker.py`, por outro lado, consegue operar com httpx estático porque o `manga_id` e o `nonce` estão embutidos no HTML inicial — não dependem de JS.

### Por que a imagem oficial do Playwright no Docker?

O Chromium exige dezenas de bibliotecas de sistema Linux (`libglib`, `libnss`, `libatk`, etc.). Instalar via `apt` manualmente no Dockerfile seria frágil, demorado e sujeito a quebrar com atualizações. A imagem `mcr.microsoft.com/playwright/python:v1.60.0-jammy` já vem com tudo pré-instalado e alinhado com a versão exata do Playwright. O tamanho (~1.5GB) é aceitável para um pipeline que roda uma vez por dia.

### Por que OAuth2 em vez de Service Account para o Google Drive?

Service Accounts têm cota de storage separada e não compartilham a cota do usuário Google. Arquivos criados por uma Service Account ficam no storage dela, não na conta pessoal do usuário. Com OAuth2, os arquivos são criados diretamente na conta Google do usuário, aproveitando os 15GB gratuitos do Google Drive pessoal.

### Por que state.json no Drive em vez de commit no repositório?

Commitar o estado no repositório exigiria configurar credenciais Git no runner, lidaria com conflitos em deploys paralelos e polui o histórico. Salvar no Drive é mais simples, mantém o estado próximo dos arquivos gerados, e funciona mesmo quando o pipeline roda em forks sem acesso de escrita ao repositório original.

### Por que `.manga-delivery-state/` separada dos arquivos de consumo?

A pasta raiz do Drive (`GDRIVE_FOLDER_ID`) é a mesma que o usuário usa para acessar os PDFs e EPUBs. Misturar `state.json` com os arquivos de leitura seria confuso. A subpasta `.manga-delivery-state/` (com ponto, como convenção Unix para "oculto") sinaliza que é infraestrutura do pipeline, não conteúdo para consumo.

### Por que Madara AJAX API em vez de RSS?

O mangalivre.to usa o plugin WordPress Madara para gerenciar o catálogo. Em instalações padrão do Madara, a rota `/feed/` é sobrescrita pelo plugin e retorna HTML vazio ou redireciona. O endpoint `ajax/chapters/` é a API interna do próprio plugin, usada pelo frontend para carregar a lista de capítulos. É mais confiável e estruturada que o RSS nesse contexto.

---

## Fluxo de branches

| Branch | Propósito |
|---|---|
| `main` | código estável, em produção |
| `develop` | integração de features — PRs vão aqui |
| `feature/*` | nova funcionalidade |
| `fix/*` | correção de bug |
| `docs/*` | apenas documentação |
| `refactor/*` | refatoração sem mudança de comportamento |

O pipeline de CI (`tests.yml`) roda em todos os PRs para `develop`. O merge de `develop` → `main` dispara o `build-image.yml` que publica a imagem atualizada no GHCR.
