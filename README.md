# manga-delivery 📦

> Pipeline de automação que monitora, baixa, converte e entrega capítulos de mangá semanalmente — direto no seu email e Google Drive.

![Pipeline Status](https://github.com/leogssantos/manga-delivery/actions/workflows/pipeline.yml/badge.svg)

---

## Como funciona

```
GitHub Actions (cron diário)
    │
    ▼
Verifica capítulo novo via Madara AJAX API (mangalivre.to)
    │
    ▼
Playwright renderiza a página e extrai URLs das imagens
    │
    ▼
Download paralelo das imagens (.webp)
    │
    ▼
Conversão → PDF + EPUB
    │
    ▼
Upload para o Google Drive (OAuth2)
    │
    ▼
Envio do EPUB por email via Gmail API
    │
    ▼
state.json atualizado no Drive (.manga-delivery-state/)
```

---

## Stack

| Componente | Tecnologia |
|---|---|
| Gerenciamento de dependências | [uv](https://github.com/astral-sh/uv) |
| Scraping / renderização JS | [Playwright](https://playwright.dev/python/) |
| HTTP | [httpx](https://www.python-httpx.org/) |
| HTML parsing | [BeautifulSoup4](https://beautiful-soup-4.readthedocs.io/) |
| Conversão de imagens | [Pillow](https://pillow.readthedocs.io/) |
| Geração de PDF | [img2pdf](https://gitlab.mister-muffin.de/josch/img2pdf) |
| Geração de EPUB | [EbookLib](https://github.com/aerkalov/ebooklib) |
| Armazenamento | Google Drive API (OAuth2) |
| Email | Gmail API (OAuth2) |
| CI/CD | GitHub Actions |

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/setup.md](docs/setup.md) | Configuração do ambiente local, instalação, testes |
| [docs/google-auth.md](docs/google-auth.md) | OAuth2 Google passo a passo (Drive + Gmail) |
| [docs/docker.md](docs/docker.md) | Uso com Docker e docker compose |
| [docs/fork-and-deploy.md](docs/fork-and-deploy.md) | Como fazer fork e rodar o pipeline no seu GitHub |
| [docs/architecture.md](docs/architecture.md) | Arquitetura, módulos e decisões técnicas |
| [docs/contributing.md](docs/contributing.md) | Como contribuir com o projeto |

---

## Quickstart

```bash
git clone https://github.com/leogssantos/manga-delivery.git
cd manga-delivery
uv sync
uv run playwright install chromium
cp .env.example .env
# edite o .env com suas credenciais
uv run python authenticate.py   # uma vez só
uv run python -m src.main
```

Para o guia completo, veja [docs/setup.md](docs/setup.md).

---

## Mangás suportados

Qualquer título disponível no [mangalivre.to](https://mangalivre.to). Para ver a lista completa:

```bash
uv run python -m src.catalog
```

Configure o slug no `.env` ou no secret `MANGA_SLUG` do GitHub Actions:

```env
MANGA_SLUG=one-piece
MANGA_SLUG=bleach
MANGA_SLUG=chainsaw-man-pt-br
```

---

## Roadmap

- [ ] Suporte a múltiplos mangás simultâneos em um único run
- [ ] Interface web simples para gerenciar slugs e destinatários
- [ ] Notificação via Telegram além do email
- [ ] Suporte a outros sites de scan (fallback automático)
- [ ] Histórico de capítulos enviados com links do Drive

---

## Contribuindo

Veja [docs/contributing.md](docs/contributing.md).

---

## Autor

**Leonardo Santos**
[GitHub](https://github.com/leogsantos/) · [LinkedIn](https://www.linkedin.com/in/leosgsantos/)

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.
