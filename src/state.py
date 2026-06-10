import json
import logging
import os
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

load_dotenv()

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
]

DEFAULT_STATE = {"last_chapter": None, "last_run": None}
STATE_FOLDER_NAME = ".manga-delivery-state"


def _get_service():
    token_file = Path(os.getenv("GDRIVE_TOKEN_FILE", "secrets/token.json"))
    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        try:
            token_file.write_text(creds.to_json(), encoding="utf-8")
        except OSError as e:
            logger.warning(f"Não foi possível salvar token renovado: {e}. Continuando sem persistir.")

    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, name: str, parent_id: str) -> str:
    """Busca ou cria uma pasta pelo nome dentro de um parent."""
    query = (
        f"name='{name}' "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    logger.info(f"Pasta criada no Drive: '{name}'")
    return folder["id"]


def _get_state_subfolder(service, slug: str) -> str:
    """
    Garante que a estrutura .manga-delivery-state/{slug} existe.
    Retorna o ID da subpasta do slug.
    """
    root_folder_id = os.getenv("GDRIVE_FOLDER_ID")
    state_folder_id = _get_or_create_folder(service, STATE_FOLDER_NAME, root_folder_id)
    slug_folder_id = _get_or_create_folder(service, slug, state_folder_id)
    return slug_folder_id


def _find_state_file(service, subfolder_id: str) -> str | None:
    """Retorna o ID do state.json no Drive ou None se não existir."""
    query = (
        f"name='state.json' "
        f"and '{subfolder_id}' in parents "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def load_state(slug: str) -> dict:
    """
    Carrega o state.json do Drive em .manga-delivery-state/{slug}/.
    Fallback para DEFAULT_STATE se não encontrar ou falhar.
    """
    try:
        service = _get_service()
        subfolder_id = _get_state_subfolder(service, slug)
        file_id = _find_state_file(service, subfolder_id)

        if not file_id:
            logger.warning(f"[{slug}] state.json não encontrado no Drive. Usando estado padrão.")
            return DEFAULT_STATE.copy()

        buffer = BytesIO()
        request = service.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        state = json.loads(buffer.getvalue().decode("utf-8"))
        logger.info(f"[{slug}] State carregado do Drive.")
        return state

    except Exception as e:
        logger.warning(f"[{slug}] Falha ao carregar state do Drive: {e}. Usando estado padrão.")
        return DEFAULT_STATE.copy()


def save_state(slug: str, chapter_url: str) -> None:
    """
    Salva o state.json no Drive em .manga-delivery-state/{slug}/.
    Atualiza se já existir, cria se não existir.
    """
    state = {
        "last_chapter": chapter_url,
        "last_run": datetime.now(timezone.utc).isoformat(),
    }
    content = json.dumps(state, indent=2).encode("utf-8")

    try:
        service = _get_service()
        subfolder_id = _get_state_subfolder(service, slug)
        file_id = _find_state_file(service, subfolder_id)

        media = MediaIoBaseUpload(BytesIO(content), mimetype="application/json")

        if file_id:
            service.files().update(fileId=file_id, media_body=media).execute()
            logger.info(f"[{slug}] state.json atualizado no Drive.")
        else:
            metadata = {
                "name": "state.json",
                "parents": [subfolder_id],
            }
            service.files().create(body=metadata, media_body=media, fields="id").execute()
            logger.info(f"[{slug}] state.json criado no Drive.")

    except Exception as e:
        logger.error(f"[{slug}] Falha ao salvar state no Drive: {e}")
