import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.exceptions import MangaDeliveryError

load_dotenv()

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class DriveUploadError(MangaDeliveryError):
    """Falha ao fazer upload de arquivo para o Google Drive."""


def _get_credentials() -> Credentials:
    token_file = Path(os.getenv("GDRIVE_TOKEN_FILE", "secrets/token.json"))
    client_file = Path(os.getenv("GDRIVE_OAUTH_CLIENT_FILE", "secrets/oauth_client.json"))

    if not token_file.exists():
        raise DriveUploadError(
            f"Token OAuth2 não encontrado em '{token_file}'. "
            "Execute 'python authenticate.py' primeiro."
        )

    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                try:
                    token_file.write_text(creds.to_json(), encoding="utf-8")
                except OSError as e:
                    logger.warning(f"Não foi possível salvar token renovado: {e}. Continuando sem persistir.")
                logger.info("Token OAuth2 renovado automaticamente.")
            except Exception as e:
                raise DriveUploadError(f"Falha ao renovar token OAuth2: {e}") from e
        else:
            raise DriveUploadError(
                "Token OAuth2 inválido e sem refresh token. "
                "Execute 'python authenticate.py' novamente."
            )

    return creds


def _get_service():
    try:
        creds = _get_credentials()
        return build("drive", "v3", credentials=creds)
    except DriveUploadError:
        raise
    except Exception as e:
        raise DriveUploadError(f"Falha ao autenticar com o Google Drive: {e}") from e


def _get_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    query = (
        f"name='{folder_name}' "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    logger.info(f"Subpasta criada no Drive: '{folder_name}'")
    return folder["id"]


def upload_file(file_path: Path, slug: str) -> str:
    """
    Faz upload de um arquivo para o Google Drive.
    Cria subpasta com o slug automaticamente.
    Retorna o link do arquivo no Drive.
    """
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    if not folder_id:
        raise DriveUploadError(
            "Variável de ambiente 'GDRIVE_FOLDER_ID' não definida."
        )

    if not file_path.exists():
        raise DriveUploadError(f"Arquivo não encontrado para upload: '{file_path}'.")

    mime_types = {
        ".pdf": "application/pdf",
        ".epub": "application/epub+zip",
    }
    mime_type = mime_types.get(file_path.suffix, "application/octet-stream")

    try:
        service = _get_service()
        subfolder_id = _get_or_create_folder(service, slug, folder_id)

        file_metadata = {
            "name": file_path.name,
            "parents": [subfolder_id],
        }
        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
        ).execute()

        link = uploaded.get("webViewLink", "")
        logger.info(f"Upload concluído: '{file_path.name}' → {link}")
        return link

    except DriveUploadError:
        raise
    except Exception as e:
        raise DriveUploadError(f"Falha ao fazer upload de '{file_path.name}': {e}") from e
