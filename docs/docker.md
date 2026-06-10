# Usando com Docker

## Sumário

- [Por que a imagem do Playwright?](#por-que-a-imagem-do-playwright)
- [Pré-requisitos](#pré-requisitos)
- [Autenticação antes de rodar](#autenticação-antes-de-rodar)
- [Rodando com docker compose](#rodando-com-docker-compose)
- [Rodando com docker run](#rodando-com-docker-run)
- [Login no GHCR (se necessário)](#login-no-ghcr-se-necessário)
- [Volumes montados](#volumes-montados)
- [Visualizando logs](#visualizando-logs)
- [Troubleshooting](#troubleshooting)

---

## Por que a imagem do Playwright?

O Chromium exige dezenas de bibliotecas de sistema Linux (`libglib`, `libnss`, `libatk`, `libdrm`, etc.). Instalar via `apt` manualmente no Dockerfile seria frágil e sujeito a quebrar com atualizações do Chromium.

A imagem base `mcr.microsoft.com/playwright/python:v1.60.0-jammy` já vem com todas as dependências pré-instaladas e alinhadas com a versão exata do Playwright usada no projeto. O tamanho maior (~1.5GB) é aceitável para um pipeline que roda uma vez ao dia.

A imagem do projeto (`ghcr.io/leogsantos/manga-delivery:latest`) é construída sobre essa base, com as dependências Python instaladas via `uv` e o código-fonte incluído.

---

## Pré-requisitos

- **Rancher Desktop** ou **Docker Desktop** com WSL2 habilitado (Windows)
- **Docker Engine** (Linux/macOS)
- Arquivos de autenticação em `secrets/` (veja [docs/google-auth.md](google-auth.md))
- Arquivo `.env` configurado (veja [docs/setup.md](setup.md))

---

## Autenticação antes de rodar

O Docker não abre browser, portanto a autenticação OAuth2 precisa ser feita localmente antes.

Se você ainda não tem o `secrets/token.json`:

```bash
uv sync
uv run python authenticate.py
```

Isso gera o `secrets/token.json` localmente. O Docker vai montar essa pasta como volume.

---

## Rodando com docker compose

O `docker-compose.yaml` já está configurado com os volumes corretos:

```bash
docker compose up
```

Para rodar em background:
```bash
docker compose up -d
```

Para ver os logs enquanto roda em background:
```bash
docker compose logs -f
```

O container executa `uv run python -m src.main` e encerra quando o pipeline termina. `restart: "no"` garante que não reinicie automaticamente.

---

## Rodando com docker run

Se preferir sem docker compose:

```bash
docker run --rm \
  --env-file .env \
  -e PYTHONUNBUFFERED=1 \
  -v $(pwd)/secrets:/app/secrets \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/downloads:/app/downloads \
  ghcr.io/leogsantos/manga-delivery:latest \
  uv run python -m src.main
```

No Windows (PowerShell), substitua `$(pwd)` por `${PWD}`:

```powershell
docker run --rm `
  --env-file .env `
  -e PYTHONUNBUFFERED=1 `
  -v ${PWD}/secrets:/app/secrets `
  -v ${PWD}/output:/app/output `
  -v ${PWD}/downloads:/app/downloads `
  ghcr.io/leogsantos/manga-delivery:latest `
  uv run python -m src.main
```

---

## Login no GHCR (se necessário)

A imagem é pública no GitHub Container Registry. Em alguns ambientes pode ser necessário autenticar:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u SEU_USUARIO --password-stdin
```

Substitua `$GITHUB_TOKEN` por um [Personal Access Token](https://github.com/settings/tokens) com permissão `read:packages`.

---

## Volumes montados

| Volume local | Caminho no container | Conteúdo |
|---|---|---|
| `./secrets` | `/app/secrets` | `oauth_client.json` e `token.json` |
| `./output` | `/app/output` | PDFs e EPUBs gerados |
| `./downloads` | `/app/downloads` | Imagens temporárias (limpas ao final do pipeline) |

As pastas `output/` e `downloads/` são criadas automaticamente se não existirem.

---

## Visualizando logs

Com docker compose:
```bash
docker compose logs
docker compose logs -f   # acompanha em tempo real
```

Com docker run (o output vai direto para o terminal pela flag `-e PYTHONUNBUFFERED=1`).

Exemplo de saída de um run com capítulo novo:
```
2025-06-01 12:00:03 [INFO] src.main: [one-piece] Iniciando pipeline...
2025-06-01 12:00:05 [INFO] src.checker: [one-piece] Novo capítulo detectado: Capítulo 1184
2025-06-01 12:00:06 [INFO] src.scraper: [one-piece] Iniciando download: https://mangalivre.to/...
2025-06-01 12:00:06 [INFO] src.scraper: [one-piece] 18 imagens encontradas. Salvando em 'downloads/one-piece/capitulo-1184'...
2025-06-01 12:00:15 [INFO] src.scraper: [one-piece] Download concluído: 18 imagens.
2025-06-01 12:00:17 [INFO] src.storage.gdrive: Upload concluído: 'one-piece-capitulo-1184.pdf' → https://drive.google.com/...
2025-06-01 12:00:19 [INFO] src.storage.gdrive: Upload concluído: 'one-piece-capitulo-1184.epub' → https://drive.google.com/...
2025-06-01 12:00:20 [INFO] src.notifier.email: Email enviado para: destino@email.com
2025-06-01 12:00:21 [INFO] src.main: [one-piece] Pipeline concluído com sucesso.
```

---

## Troubleshooting

### `Cannot connect to the Docker daemon`

O Docker daemon não está rodando. Inicie o Rancher Desktop ou Docker Desktop e aguarde estar pronto.

### `error during connect: ... pipe/docker_engine`  (Windows)

O contexto do Docker pode estar errado. Verifique:

```powershell
docker context ls
```

Se o contexto ativo não for o correto, troque:

```powershell
docker context use rancher-desktop
# ou
docker context use default
```

### `manifest unknown` ao baixar a imagem

A imagem pode não existir ainda para sua plataforma (ARM vs x86). Verifique se há um build disponível em [ghcr.io/leogsantos/manga-delivery](https://github.com/leogsantos/manga-delivery/pkgs/container/manga-delivery).

### Container sai com código 0 sem fazer nada

Provavelmente não há capítulo novo. Verifique os logs — deve aparecer `Nenhum capítulo novo. Encerrando.` O pipeline funciona corretamente.

### Token OAuth2 inválido dentro do container

Verifique se o volume `./secrets` está montado corretamente e se o arquivo `secrets/token.json` existe localmente. Se não existir, rode `uv run python authenticate.py` fora do container primeiro.
