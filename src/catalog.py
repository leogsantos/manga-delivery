import logging
import httpx
from xml.etree import ElementTree as ET

from src.exceptions import MangaDeliveryError, BotBlockedError
from src.utils import BROWSER_HEADERS

logger = logging.getLogger(__name__)

SITEMAP_URL = "https://mangalivre.to/wp-manga-sitemap.xml"
BASE_URL = "https://mangalivre.to/manga/"


def _extract_slug(url: str) -> str:
    """Extrai o slug a partir da URL do sitemap."""
    return url.rstrip("/").replace(BASE_URL, "")


def _fetch_sitemap() -> str:
    """Faz o GET no sitemap e retorna o XML como string."""
    try:
        resp = httpx.get(SITEMAP_URL, timeout=15, follow_redirects=True, headers=BROWSER_HEADERS)

        if resp.status_code == 418:
            raise BotBlockedError(
                "O site bloqueou a requisição (418 I'm a teapot). "
                "Isso geralmente indica ausência ou invalidade do User-Agent. "
                "Verifique o BROWSER_HEADERS em src/utils.py."
            )

        resp.raise_for_status()
        return resp.text

    except BotBlockedError:
        raise
    except httpx.HTTPError as e:
        raise MangaDeliveryError(f"Falha ao acessar sitemap: {e}") from e


def list_available_manga() -> list[dict]:
    """Busca todos os mangás disponíveis no sitemap."""
    xml_content = _fetch_sitemap()
    root = ET.fromstring(xml_content)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    mangas = []
    for url_el in root.findall("sm:url", namespace):
        loc = url_el.findtext("sm:loc", namespaces=namespace)
        lastmod = url_el.findtext("sm:lastmod", namespaces=namespace)
        if loc and loc.startswith(BASE_URL) and loc.rstrip("/") != BASE_URL.rstrip("/"):
            mangas.append({
                "slug": _extract_slug(loc),
                "last_update": lastmod,
            })

    return sorted(mangas, key=lambda x: x["last_update"] or "", reverse=True)


def print_catalog() -> None:
    mangas = list_available_manga()
    print(f"\n{'SLUG':<50} {'ÚLTIMO UPDATE'}")
    print("-" * 70)
    for m in mangas:
        print(f"{m['slug']:<50} {m['last_update'] or 'N/A'}")
    print(f"\nTotal: {len(mangas)} títulos\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    print_catalog()
