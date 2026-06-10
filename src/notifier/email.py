import base64
import logging
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.exceptions import MangaDeliveryError

load_dotenv()

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
]


class EmailSendError(MangaDeliveryError):
    """Falha ao enviar email via Gmail API."""


def _get_credentials() -> Credentials:
    token_file = Path(os.getenv("GDRIVE_TOKEN_FILE", "secrets/token.json"))

    if not token_file.exists():
        raise EmailSendError(
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
                raise EmailSendError(f"Falha ao renovar token OAuth2: {e}") from e
        else:
            raise EmailSendError(
                "Token OAuth2 inválido. Execute 'python authenticate.py' novamente."
            )

    return creds


def _build_message(
    sender: str,
    recipients: list[str],
    subject: str,
    body: str,
    attachment_path: Path,
) -> dict:
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html", "utf-8"))

    with attachment_path.open("rb") as f:
        part = MIMEApplication(f.read(), Name=attachment_path.name)
        part["Content-Disposition"] = f'attachment; filename="{attachment_path.name}"'
        msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def send_chapter_email(
    slug: str,
    chapter_title: str,
    epub_path: Path,
    drive_link: str,
) -> None:
    """
    Envia email com o EPUB anexado e link do Drive.
    """
    sender = os.getenv("GMAIL_FROM")
    recipients_raw = os.getenv("GMAIL_TO", "")
    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    if not sender:
        raise EmailSendError("Variável 'GMAIL_FROM' não definida.")
    if not recipients:
        raise EmailSendError("Variável 'GMAIL_TO' não definida ou vazia.")
    if not epub_path.exists():
        raise EmailSendError(f"Arquivo EPUB não encontrado: '{epub_path}'.")

    manga_name = slug.replace("-", " ").title()
    subject = f"📦 {manga_name} — {chapter_title} disponível"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>📦 {manga_name} — {chapter_title}</h2>
        <p>O novo capítulo foi baixado, convertido e salvo com sucesso.</p>
        <ul>
            <li>✅ Arquivo <strong>.epub</strong> anexado neste email</li>
            <li>☁️ Arquivos salvos no Google Drive: <a href="{drive_link}">{drive_link}</a></li>
        </ul>
        <p style="color: #888; font-size: 12px;">Enviado automaticamente pelo manga-delivery 🤖</p>
    </body>
    </html>
    """

    try:
        creds = _get_credentials()
        service = build("gmail", "v1", credentials=creds)

        message = _build_message(sender, recipients, subject, body, epub_path)
        service.users().messages().send(userId="me", body=message).execute()

        logger.info(f"Email enviado para: {', '.join(recipients)}")

    except EmailSendError:
        raise
    except Exception as e:
        raise EmailSendError(f"Falha ao enviar email: {e}") from e
