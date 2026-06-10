import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
]
CLIENT_FILE = Path(os.getenv("GDRIVE_OAUTH_CLIENT_FILE", "secrets/oauth_client.json"))
TOKEN_FILE = Path(os.getenv("GDRIVE_TOKEN_FILE", "secrets/token.json"))


def authenticate() -> Credentials:
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("Token renovado automaticamente.")
        else:
            print(f"Lendo client file: {CLIENT_FILE.absolute()}")
            print(f"Existe: {CLIENT_FILE.exists()}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            print("Autenticação concluída.")

        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        print(f"Token salvo em: {TOKEN_FILE}")

    return creds

if __name__ == "__main__":
    creds = authenticate()
    print("Autenticado com sucesso.")