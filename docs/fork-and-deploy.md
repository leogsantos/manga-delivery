# Fork e deploy do próprio pipeline

## Sumário

- [Visão geral](#visão-geral)
- [Passo 1 — Fork do repositório](#passo-1--fork-do-repositório)
- [Passo 2 — Criar projeto no Google Cloud](#passo-2--criar-projeto-no-google-cloud)
- [Passo 3 — Ativar as APIs](#passo-3--ativar-as-apis)
- [Passo 4 — Configurar tela de consentimento e criar OAuth2 Client ID](#passo-4--configurar-tela-de-consentimento-e-criar-oauth2-client-id)
- [Passo 5 — Autenticar localmente](#passo-5--autenticar-localmente)
- [Passo 6 — Criar pasta no Google Drive](#passo-6--criar-pasta-no-google-drive)
- [Passo 7 — Minificar os JSONs](#passo-7--minificar-os-jsons)
- [Passo 8 — Adicionar secrets e variáveis no GitHub](#passo-8--adicionar-secrets-e-variáveis-no-github)
- [Passo 9 — Testar manualmente](#passo-9--testar-manualmente)
- [Tabela completa de secrets e variáveis](#tabela-completa-de-secrets-e-variáveis)
- [Trocando o mangá monitorado](#trocando-o-mangá-monitorado)
- [Múltiplos mangás (extensão futura)](#múltiplos-mangás-extensão-futura)

---

## Visão geral

O manga-delivery foi projetado para ser fácil de forkar e rodar no GitHub Actions da sua própria conta. Cada pessoa tem sua própria instância com seus próprios secrets, pasta no Drive e email configurado.

O pipeline roda automaticamente todo dia ao meio-dia UTC (09h horário de Brasília). Você também pode disparar manualmente pelo GitHub.

---

## Passo 1 — Fork do repositório

1. Acesse [github.com/leogssantos/manga-delivery](https://github.com/leogssantos/manga-delivery)
2. Clique em **Fork** → **Create fork**
3. Clone o fork localmente:

```bash
git clone https://github.com/SEU_USUARIO/manga-delivery.git
cd manga-delivery
```

4. Instale as dependências para rodar o `authenticate.py`:

```bash
uv sync
```

---

## Passo 2 — Criar projeto no Google Cloud

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. No seletor de projeto (topo da página) → **Novo projeto**
3. Nome: `manga-delivery` (qualquer nome)
4. Clique em **Criar**

---

## Passo 3 — Ativar as APIs

No projeto criado:

1. **APIs e Serviços** → **Biblioteca**
2. Pesquise e ative **Google Drive API**
3. Pesquise e ative **Gmail API**

---

## Passo 4 — Configurar tela de consentimento e criar OAuth2 Client ID

### Tela de consentimento

1. **APIs e Serviços** → **Tela de consentimento OAuth**
2. Tipo: **Externo** → **Criar**
3. Preencha nome do app e email de suporte
4. Avance pelas telas até chegar em **Usuários de teste**
5. Adicione seu email → **Salvar e continuar**

### OAuth2 Client ID

1. **APIs e Serviços** → **Credenciais** → **Criar credenciais** → **ID do cliente OAuth2**
2. Tipo: **App para computador**
3. Nome: `manga-delivery`
4. **Criar** → **Baixar JSON**
5. Salve como `secrets/oauth_client.json`

Para instruções detalhadas, veja [docs/google-auth.md](google-auth.md).

---

## Passo 5 — Autenticar localmente

```bash
uv run python authenticate.py
```

O browser vai abrir. Faça login com a conta Google que será usada para Drive e Gmail. Clique em "Avançado" → "Acessar manga-delivery (não seguro)" → autorize os escopos.

Após a autorização, o arquivo `secrets/token.json` é criado.

> **⚠️ Atenção:** Este passo precisa ser feito **uma vez por máquina**. O token gerado tem refresh token e se renova automaticamente.

---

## Passo 6 — Criar pasta no Google Drive

1. Acesse [drive.google.com](https://drive.google.com) com a mesma conta usada na autenticação
2. Crie uma pasta chamada `manga-delivery`
3. Abra a pasta e copie o ID da URL:

```
https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUv
                                        ^^^^^^^^^^^^^^^^^^^^^^^^
                                        GDRIVE_FOLDER_ID
```

O pipeline criará automaticamente subpastas dentro dela (uma por mangá, mais `.manga-delivery-state/`).

---

## Passo 7 — Minificar os JSONs

O GitHub Secrets exige valores em uma única linha. Minifique os JSONs antes de adicioná-los.

### PowerShell (Windows)

```powershell
# Copia token.json minificado para a área de transferência
(Get-Content "secrets/token.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Compress) | Set-Clipboard

# Copia oauth_client.json minificado para a área de transferência
(Get-Content "secrets/oauth_client.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Compress) | Set-Clipboard
```

### Linux/macOS

```bash
# token.json
cat secrets/token.json | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)))"

# oauth_client.json
cat secrets/oauth_client.json | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)))"
```

---

## Passo 8 — Adicionar secrets e variáveis no GitHub

No repositório forkado, vá em **Settings** → **Secrets and variables** → **Actions**.

### Secrets (aba Secrets)

Clique em **New repository secret** para cada um:

| Secret | Valor |
|---|---|
| `GDRIVE_TOKEN_JSON` | Conteúdo minificado do `secrets/token.json` |
| `GDRIVE_OAUTH_CLIENT_JSON` | Conteúdo minificado do `secrets/oauth_client.json` |
| `GDRIVE_FOLDER_ID` | ID da pasta no Google Drive |
| `GMAIL_FROM` | Email remetente (mesma conta autenticada) |
| `GMAIL_TO` | Emails destinatários separados por vírgula |

### Variáveis (aba Variables)

Clique em **New repository variable**:

| Variável | Valor |
|---|---|
| `MANGA_SLUG` | Slug do mangá (ex: `one-piece`) |

> **💡 Dica:** `MANGA_SLUG` é uma variável (não secret) porque não é dado sensível. No workflow é referenciado como `${{ vars.MANGA_SLUG }}`.

---

## Passo 9 — Testar manualmente

1. No repositório, vá em **Actions** → **manga-delivery pipeline**
2. Clique em **Run workflow** → **Run workflow**
3. Acompanhe a execução em tempo real

Se for o primeiro run e o mangá tiver capítulos, o pipeline vai baixar, converter, fazer upload e enviar o email.

Se já houver um `state.json` no Drive do run anterior, o pipeline só vai agir se houver capítulo novo.

> **💡 Dica:** Para forçar o pipeline a baixar novamente (ex: para testar), delete o arquivo `.manga-delivery-state/{slug}/state.json` no Google Drive.

---

## Tabela completa de secrets e variáveis

| Nome | Tipo | Descrição |
|---|---|---|
| `GDRIVE_TOKEN_JSON` | Secret | JSON minificado do `token.json` gerado pelo `authenticate.py`. Contém o refresh token OAuth2. |
| `GDRIVE_OAUTH_CLIENT_JSON` | Secret | JSON minificado do `oauth_client.json` baixado do Google Cloud Console. Contém o client_id e client_secret. |
| `GDRIVE_FOLDER_ID` | Secret | ID da pasta raiz no Google Drive. Obtido da URL da pasta. |
| `GMAIL_FROM` | Secret | Email remetente. Deve ser o mesmo email da conta Google autenticada. |
| `GMAIL_TO` | Secret | Destinatários separados por vírgula. Ex: `leitor1@gmail.com,leitor2@outlook.com` |
| `MANGA_SLUG` | Variable | Slug do mangá no mangalivre.to. Ex: `one-piece`, `bleach`, `chainsaw-man-pt-br` |

---

## Trocando o mangá monitorado

1. Encontre o novo slug com o catálogo:

```bash
uv run python -m src.catalog
```

2. No GitHub, vá em **Settings** → **Secrets and variables** → **Actions** → aba **Variables**
3. Edite `MANGA_SLUG` com o novo slug
4. Na próxima execução, o pipeline vai iniciar do zero para o novo mangá

> **⚠️ Atenção:** Ao trocar o slug, não há `state.json` para o novo mangá. O pipeline vai considerar o capítulo mais recente como "novo" e fazer o download na primeira execução.

---

## Múltiplos mangás (extensão futura)

A versão atual suporta apenas um mangá por vez (um slug por instância). Para acompanhar múltiplos títulos, as opções são:

**Opção 1 — Múltiplos repositórios forkados:** Fork o projeto para cada mangá, cada um com seu próprio `MANGA_SLUG`. Simples mas não escala bem.

**Opção 2 — Modificar `src/main.py`:** Ler `MANGA_SLUG` como lista separada por vírgula e iterar, chamando o pipeline completo para cada slug. Contribuições são bem-vindas — veja [docs/contributing.md](contributing.md).

**Opção 3 — Matrix no GitHub Actions:** Usar `strategy.matrix` no workflow para rodar um job paralelo por slug. Requer refatoração do workflow.
