import re
import logging
import httpx
from bs4 import BeautifulSoup

from src.exceptions import (
    BotBlockedError,
    PageFetchError,
    NonceMissingError,
    ChapterFetchError,
    ChapterParseError,
)
from src.state import load_state
from src.utils import retry, BROWSER_HEADERS

logger = logging.getLogger(__name__)

BASE_URL = "https://mangalivre.to"


def _fetch_page(slug: str) -> str:
    url = f"{BASE_URL}/manga/{slug}/"
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True, headers=BROWSER_HEADERS)

        if resp.status_code == 418:
            raise BotBlockedError(
                f"Site bloqueou a requisição ao acessar a página do mangá '{slug}' (418). "
                "Verifique o BROWSER_HEADERS em src/utils.py."
            )

        resp.raise_for_status()
        return resp.text

    except BotBlockedError:
        raise
    except httpx.HTTPError as e:
        raise PageFetchError(f"Falha ao acessar página do mangá '{slug}': {e}") from e


def _extract_page_meta(slug: str) -> tuple[str, str]:
    """Extrai manga_id e nonce da página do mangá."""
    html = _fetch_page(slug)

    manga_id_match = re.search(r'"manga_id"\s*:\s*"?(\d+)"?', html)
    nonce_match = re.search(r'"nonce"\s*:\s*"([^"]+)"', html)

    if not manga_id_match or not nonce_match:
        raise NonceMissingError(
            f"manga_id ou nonce não encontrado na página do mangá '{slug}'. "
            "A estrutura da página pode ter mudado."
        )

    return manga_id_match.group(1), nonce_match.group(1)


@retry(max_attempts=3, base_delay=2.0, exceptions=(ChapterFetchError,))
def _fetch_chapters(slug: str, manga_id: str, nonce: str) -> list[dict]:
    """Chama a Madara AJAX API e retorna lista de capítulos."""
    url = f"{BASE_URL}/manga/{slug}/ajax/chapters/"
    try:
        resp = httpx.post(
            url,
            data={
                "action": "manga-chapters-order",
                "manga": manga_id,
                "nonce": nonce,
            },
            headers={
                **BROWSER_HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=15,
        )

        if resp.status_code == 418:
            raise BotBlockedError(
                f"Site bloqueou a requisição AJAX de capítulos para '{slug}' (418). "
                "Verifique o BROWSER_HEADERS em src/utils.py."
            )

        resp.raise_for_status()

    except BotBlockedError:
        raise
    except httpx.HTTPError as e:
        raise ChapterFetchError(f"Falha na AJAX API para '{slug}': {e}") from e

    try:
        soup = BeautifulSoup(resp.text, "lxml")
        chapters = []
        for li in soup.select("li.wp-manga-chapter"):
            a = li.select_one("a")
            date = li.select_one(".chapter-release-date i")
            if a:
                chapters.append({
                    "title": a.text.strip(),
                    "url": a["href"],
                    "date": date.text.strip() if date else None,
                })
        return chapters

    except Exception as e:
        raise ChapterParseError(f"Falha ao parsear capítulos de '{slug}': {e}") from e


def get_latest_chapter(slug: str) -> dict | None:
    """
    Retorna o capítulo mais recente se for novo, None se já foi processado.
    """
    manga_id, nonce = _extract_page_meta(slug)
    chapters = _fetch_chapters(slug, manga_id, nonce)

    if not chapters:
        logger.warning(f"[{slug}] Nenhum capítulo encontrado.")
        return None

    latest = chapters[0]
    state = load_state(slug)

    if latest["url"] == state.get("last_chapter"):
        logger.info(f"[{slug}] Sem capítulo novo. Último: {latest['title']}")
        return None

    logger.info(f"[{slug}] Novo capítulo detectado: {latest['title']}")
    return latest