# Autenticação Google OAuth2

## Sumário

- [Visão geral](#visão-geral)
- [1. Criar projeto no Google Cloud Console](#1-criar-projeto-no-google-cloud-console)
- [2. Ativar as APIs](#2-ativar-as-apis)
- [3. Configurar a tela de consentimento OAuth](#3-configurar-a-tela-de-consentimento-oauth)
- [4. Criar o OAuth2 Client ID](#4-criar-o-oauth2-client-id)
- [5. Adicionar usuário de teste](#5-adicionar-usuário-de-teste)
- [6. Rodar o authenticate.py](#6-rodar-o-authenticatepy)
- [7. O aviso "Google não verificou este app"](#7-o-aviso-google-não-verificou-este-app)
- [8. Minificar os JSONs para o GitHub Actions](#8-minificar-os-jsons-para-o-github-actions)
- [9. Adicionar secrets no GitHub](#9-adicionar-secrets-no-github)
- [Como o refresh token funciona](#como-o-refresh-token-funciona)

---

## Visão geral

O pipeline usa OAuth2 com escopo de usuário para autenticar com o Google Drive e o Gmail. Isso significa que os arquivos são criados na conta Google do usuário (não em uma Service Account) e usam a cota de storage pessoal.

O fluxo de autenticação precisa ser feito **uma única vez** localmente. O `authenticate.py` abre o browser para autorização e salva o `token.json` com o refresh token. A partir daí, o token é renovado automaticamente sempre que necessário — tanto localmente quanto no GitHub Actions.

Você vai precisar de dois arquivos:
- `secrets/oauth_client.json` — credenciais do app (baixado do Google Cloud Console)
- `secrets/token.json` — token de acesso + refresh token (gerado pelo `authenticate.py`)

---

## 1. Criar projeto no Google Cloud Console

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. No menu superior, clique no seletor de projeto → **Novo projeto**
3. Nome: `manga-delivery` (qualquer nome serve)
4. Clique em **Criar** e aguarde

---

## 2. Ativar as APIs

Com o projeto selecionado:

1. No menu lateral, vá em **APIs e Serviços** → **Biblioteca**
2. Pesquise e ative **Google Drive API**:
   - Clique na API → **Ativar**
3. Volte para a Biblioteca, pesquise e ative **Gmail API**:
   - Clique na API → **Ativar**

---

## 3. Configurar a tela de consentimento OAuth

Antes de criar as credenciais, configure a tela que aparece quando o usuário autoriza o app.

1. No menu lateral, vá em **APIs e Serviços** → **Tela de consentimento OAuth**
2. Tipo de usuário: **Externo** → **Criar**
3. Preencha os campos obrigatórios:
   - **Nome do app:** `manga-delivery`
   - **Email de suporte do usuário:** seu email
   - **Informações de contato do desenvolvedor:** seu email
4. Clique em **Salvar e continuar**
5. Na tela de **Escopos**, clique em **Salvar e continuar** (sem adicionar nada)
6. Na tela de **Usuários de teste**, adicione seu email (veja a seção seguinte)
7. Clique em **Salvar e continuar** → **Voltar para o painel**

---

## 4. Criar o OAuth2 Client ID

1. No menu lateral, vá em **APIs e Serviços** → **Credenciais**
2. Clique em **Criar credenciais** → **ID do cliente OAuth2**
3. Tipo de aplicativo: **App para computador**
4. Nome: `manga-delivery`
5. Clique em **Criar**
6. Na janela que abre, clique em **Baixar JSON**
7. Salve o arquivo como `secrets/oauth_client.json` na raiz do repositório

> **⚠️ Atenção:** O arquivo `secrets/` está no `.gitignore`. Nunca comite o `oauth_client.json` ou o `token.json` no repositório.

---

## 5. Adicionar usuário de teste

Como o app está em modo de desenvolvimento (não verificado pelo Google), apenas emails cadastrados como "usuários de teste" podem autorizar o acesso.

1. Vá em **APIs e Serviços** → **Tela de consentimento OAuth**
2. Na seção **Usuários de teste**, clique em **Adicionar usuários**
3. Adicione o email da conta Google que será usada para Drive e Gmail
4. Clique em **Salvar**

> **💡 Dica:** Use o mesmo email que será configurado em `GMAIL_FROM`. É a conta que vai enviar os emails e onde os arquivos serão salvos no Drive.

---

## 6. Rodar o authenticate.py

Com o `oauth_client.json` na pasta `secrets/`, execute:

```bash
uv run python authenticate.py
```

O script vai:
1. Abrir o browser com a tela de autorização do Google
2. Pedir para você fazer login (se não estiver logado) e autorizar os escopos
3. Salvar o `secrets/token.json` automaticamente

Saída esperada:
```
Lendo client file: /caminho/para/secrets/oauth_client.json
Existe: True
Autenticação concluída.
Token salvo em: secrets/token.json
Autenticado com sucesso.
```

---

## 7. O aviso "Google não verificou este app"

Durante a autorização, o Google exibe um aviso de segurança porque o app está em modo de teste e não passou pelo processo de verificação do Google.

Como proceder:
1. Na tela de aviso, clique em **Avançado** (link discreto no canto inferior esquerdo)
2. Clique em **Acessar manga-delivery (não seguro)**
3. Revise os escopos solicitados e clique em **Continuar**

Isso é esperado e seguro — você está autorizando seu próprio app a acessar sua própria conta.

---

## 8. Minificar os JSONs para o GitHub Actions

O GitHub Secrets não aceita quebras de linha nos valores. Os JSONs precisam ser minificados para uma única linha antes de serem adicionados como secrets.

### No PowerShell (Windows)

```powershell
# token.json — copia para a área de transferência
(Get-Content "secrets/token.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Compress) | Set-Clipboard

# oauth_client.json — copia para a área de transferência
(Get-Content "secrets/oauth_client.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Compress) | Set-Clipboard
```

### No Linux/macOS

```bash
# token.json
cat secrets/token.json | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)))" | pbcopy

# oauth_client.json
cat secrets/oauth_client.json | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)))" | pbcopy
```

No Linux sem `pbcopy`:
```bash
cat secrets/token.json | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)))"
# copie o output manualmente
```

> **💡 Dica:** Verifique se o resultado é mesmo uma única linha antes de colar no GitHub. Deve começar com `{"token_type":...` sem nenhuma quebra de linha.

---

## 9. Adicionar secrets no GitHub

1. No repositório, vá em **Settings** → **Secrets and variables** → **Actions**
2. Clique em **New repository secret** e adicione cada um:

| Secret | Valor |
|---|---|
| `GDRIVE_TOKEN_JSON` | Conteúdo minificado do `secrets/token.json` |
| `GDRIVE_OAUTH_CLIENT_JSON` | Conteúdo minificado do `secrets/oauth_client.json` |
| `GDRIVE_FOLDER_ID` | ID da pasta no Google Drive |
| `GMAIL_FROM` | Email remetente |
| `GMAIL_TO` | Emails destinatários separados por vírgula |

3. Para o `MANGA_SLUG`, vá em **Settings** → **Secrets and variables** → **Actions** → aba **Variables** → **New repository variable**:

| Variável | Valor |
|---|---|
| `MANGA_SLUG` | Slug do mangá (ex: `one-piece`) |

> **⚠️ Atenção:** `MANGA_SLUG` usa **Variables** (não Secrets) porque não é dado sensível. No workflow, ele é referenciado como `${{ vars.MANGA_SLUG }}`.

---

## Como o refresh token funciona

O `token.json` contém dois tokens:
- **access_token** — token de curta duração (válido por ~1 hora)
- **refresh_token** — token de longa duração, usado para renovar o access_token automaticamente

Quando o pipeline roda e o `access_token` está expirado, o código em `storage/gdrive.py` e `notifier/email.py` chama `creds.refresh(Request())` automaticamente antes de qualquer chamada à API. O `token.json` é atualizado com o novo `access_token`.

No GitHub Actions, o arquivo é recriado a partir do secret a cada execução, então o token renovado não persiste entre runs. Isso não é problema porque o `refresh_token` não expira (a não ser que você revogue o acesso nas configurações da conta Google).

> **⚠️ Atenção:** Se você revogar o acesso em [myaccount.google.com/permissions](https://myaccount.google.com/permissions), o `refresh_token` invalida e você precisa rodar `authenticate.py` novamente e atualizar o secret `GDRIVE_TOKEN_JSON`.
