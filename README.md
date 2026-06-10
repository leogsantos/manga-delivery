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
Conversão → PDF + EPUB (compressão automática)
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
 
> **Por que a imagem Playwright oficial?**
> O Chromium exige dezenas de dependências de sistema Linux. A imagem `mcr.microsoft.com/playwright/python` já vem com tudo instalado, evitando complexidade de `apt` manual. O tamanho maior (~1.5GB) é aceitável para um pipeline semanal.
 
---
 
## Pré-requisitos
 
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) instalado
- Conta Google (para Drive e Gmail)
- Projeto no [Google Cloud Console](https://console.cloud.google.com) com:
  - Google Drive API ativada
  - Gmail API ativada
  - OAuth2 Client ID configurado (tipo: App para computador)
---
 
## Configuração
 
### 1. Clone o repositório
 
```bash
git clone https://github.com/leogssantos/manga-delivery.git
cd manga-delivery
```
 
### 2. Instala dependências
 
```bash
uv sync
uv run playwright install chromium
```
 
### 3. Configura o Google Cloud
 
#### 3.1 Cria o projeto e ativa as APIs
 
- Acessa [console.cloud.google.com](https://console.cloud.google.com)
- Cria um novo projeto (ex: `manga-delivery`)
- Ativa a **Google Drive API**
- Ativa a **Gmail API**
#### 3.2 Cria o OAuth2 Client ID
 
- Menu → "APIs e Serviços" → "Credenciais"
- "Criar credenciais" → "ID do cliente OAuth2"
- Tipo: **App para computador**
- Nome: `manga-delivery`
- Baixa o JSON → salva como `secrets/oauth_client.json`
#### 3.3 Configura a tela de consentimento
 
- Menu → "APIs e Serviços" → "Tela de consentimento OAuth"
- Tipo: **Externo**
- Preenche nome do app e email de suporte
- Em **Usuários de teste** adiciona seu email do Google
#### 3.4 Autentica localmente (obrigatório — apenas uma vez)
 
```bash
uv run python authenticate.py
```
 
O browser vai abrir pedindo autorização. Após autorizar, o arquivo `secrets/token.json` é gerado automaticamente. O token se renova sozinho a partir daí — você não precisa repetir esse passo.
 
> **Atenção:** vai aparecer um aviso "O Google não verificou este app". Clique em "Avançado" → "Acessar manga-delivery (não seguro)". Isso é esperado para apps em modo de teste.
 
### 4. Cria a pasta no Google Drive
 
- Acessa [drive.google.com](https://drive.google.com)
- Cria uma pasta chamada `manga-delivery`
- Copia o ID da pasta na URL: `drive.google.com/drive/folders/**SEU_FOLDER_ID**`
### 5. Configura o `.env`
 
Copia o `.env.example` e preenche:
 
```bash
cp .env.example .env
```
 
```env
GDRIVE_OAUTH_CLIENT_FILE=secrets/oauth_client.json
GDRIVE_TOKEN_FILE=secrets/token.json
GDRIVE_FOLDER_ID=seu_folder_id_aqui
MANGA_SLUG=one-piece
GMAIL_FROM=seu@gmail.com
GMAIL_TO=destino1@email.com,destino2@email.com
```
 
### 6. Testa localmente
 
```bash
uv run python -m src.main
```
 
---
 
## Configuração no GitHub Actions
 
Para rodar automaticamente via CI, você precisa adicionar os secrets no repositório.
 
### Passo 1 — Minifica os JSONs para uma linha
 
No PowerShell (Windows):
 
```powershell
# token.json
(Get-Content "secrets/token.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Compress) | Set-Clipboard
```
 
```powershell
# oauth_client.json
(Get-Content "secrets/oauth_client.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Compress) | Set-Clipboard
```
 
No Linux/macOS:
 
```bash
# token.json
cat secrets/token.json | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)))" | pbcopy
 
# oauth_client.json
cat secrets/oauth_client.json | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)))" | pbcopy
```
 
### Passo 2 — Adiciona os secrets no GitHub
 
Acessa **Settings → Secrets and variables → Actions → New repository secret** e adiciona:
 
| Secret | Valor |
|---|---|
| `GDRIVE_TOKEN_JSON` | conteúdo minificado do `token.json` |
| `GDRIVE_OAUTH_CLIENT_JSON` | conteúdo minificado do `oauth_client.json` |
| `GDRIVE_FOLDER_ID` | ID da pasta no Google Drive |
| `MANGA_SLUG` | slug do mangá (ex: `one-piece`) |
| `GMAIL_FROM` | email remetente |
| `GMAIL_TO` | emails destinatários separados por vírgula |
 
### Passo 3 — Dispara manualmente para testar
 
Acessa **Actions → manga-delivery pipeline → Run workflow**.
 
O pipeline também roda automaticamente todo dia ao meio-dia UTC (09h horário de Brasília).
 
---
 
## Estrutura do projeto
 
```
manga-delivery/
├── .github/
│   └── workflows/
│       └── pipeline.yml        # GitHub Actions cron + CI
├── .devcontainer/
│   ├── devcontainer.json
│   └── setup.sh
├── src/
│   ├── main.py                 # orquestra o pipeline
│   ├── checker.py              # detecta capítulo novo (Madara AJAX API)
│   ├── scraper.py              # download das imagens via Playwright
│   ├── state.py                # lê/escreve state.json no Google Drive
│   ├── catalog.py              # lista mangás disponíveis no site
│   ├── exceptions.py           # exceptions customizadas
│   ├── utils.py                # utilitários (retry, headers)
│   ├── converter/
│   │   ├── __init__.py         # conversão webp → jpeg compartilhada
│   │   ├── to_pdf.py           # imagens → PDF
│   │   └── to_epub.py          # imagens → EPUB
│   ├── storage/
│   │   └── gdrive.py           # upload para o Google Drive
│   └── notifier/
│       └── email.py            # envio de email via Gmail API
├── secrets/                    # credenciais locais (gitignored)
│   ├── oauth_client.json
│   └── token.json
├── authenticate.py             # autenticação OAuth2 (roda uma vez)
├── pyproject.toml
├── .python-version
├── .env.example
└── .gitignore
```
 
---
 
## Mangás suportados
 
O projeto suporta qualquer mangá disponível no [mangalivre.to](https://mangalivre.to). Para ver a lista completa:
 
```bash
uv run python -m src.catalog
```
 
Troca o slug no `.env` ou na variável `MANGA_SLUG` do GitHub Actions:
 
```env
MANGA_SLUG=naruto
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
- [ ] Geração de CBZ (formato para leitores de quadrinhos)
---
 
## Contribuindo
 
Contribuições são bem-vindas! Veja o [CONTRIBUTING.md](CONTRIBUTING.md) para saber como.
 
---
 
## Autor
 
**Leonardo Santos**
[GitHub](https://github.com/leogssantos) · [LinkedIn](https://linkedin.com/in/leogssantos)
 
---
 
## Licença
 
MIT — veja [LICENSE](LICENSE) para detalhes.
