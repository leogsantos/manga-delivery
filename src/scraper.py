import asyncio
import logging
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from src.exceptions import BotBlockedError, PageFetchError, ChapterParseError
from src.utils import BROWSER_HEADERS

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = Path("downloads")


def _fetch_chapter_html(url: str) -> str:
    """Renderiza a página via Playwright para obter HTML com imagens carregadas."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000) #60s
            html = page.content()
            browser.close()
        return html
    except Exception as e:
        raise PageFetchError(f"Falha ao renderizar página do capítulo '{url}': {e}") from e


def _extract_image_urls(html: str, chapter_url: str) -> list[str]:
    """Extrai URLs das imagens do capítulo via classe wp-manga-chapter-img."""
    soup = BeautifulSoup(html, "lxml")
    imgs = soup.find_all("img", class_="wp-manga-chapter-img")

    if not imgs:
        raise ChapterParseError(
            f"Nenhuma imagem encontrada na página '{chapter_url}'. "
            "A estrutura do site pode ter mudado."
        )

    urls = [img["src"].strip() for img in imgs if img.get("src")]

    if not urls:
        raise ChapterParseError(f"Lista de imagens vazia para o capítulo '{chapter_url}'.")

    return urls


def _resolve_output_dir(slug: str, chapter_url: str) -> Path:
    match = re.search(r"capitulo-([\d\-]+)/?$", chapter_url.rstrip("/"))
    chapter_id = match.group(1) if match else "desconhecido"
    output_dir = DOWNLOADS_DIR / slug / f"capitulo-{chapter_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


async def _download_image(
    client: httpx.AsyncClient,
    url: str,
    dest: Path,
    semaphore: asyncio.Semaphore,
) -> Path:
    async with semaphore:
        try:
            resp = await client.get(url, timeout=30, headers=BROWSER_HEADERS)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            logger.debug(f"Baixado: {dest.name}")
            return dest
        except httpx.HTTPError as e:
            logger.error(f"Falha ao baixar imagem '{url}': {e}")
            raise


async def _download_all(image_urls: list[str], output_dir: Path) -> list[Path]:
    semaphore = asyncio.Semaphore(5)
    paths = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = []
        for i, url in enumerate(image_urls):
            ext = Path(url.split("?")[0]).suffix or ".webp"
            dest = output_dir / f"{str(i + 1).zfill(3)}{ext}"
            tasks.append(_download_image(client, url, dest, semaphore))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            raise ChapterParseError(f"Falha ao baixar uma ou mais imagens: {r}")
        paths.append(r)

    return sorted(paths)


def download_chapter(slug: str, chapter_url: str) -> list[Path]:
    logger.info(f"[{slug}] Iniciando download: {chapter_url}")

    html = _fetch_chapter_html(chapter_url)
    image_urls = _extract_image_urls(html, chapter_url)
    output_dir = _resolve_output_dir(slug, chapter_url)

    logger.info(f"[{slug}] {len(image_urls)} imagens encontradas. Salvando em '{output_dir}'...")

    paths = asyncio.run(_download_all(image_urls, output_dir))

    logger.info(f"[{slug}] Download concluído: {len(paths)} imagens.")
    return paths


def cleanup_chapter(slug: str, chapter_url: str) -> None:
    output_dir = _resolve_output_dir(slug, chapter_url)

    if not output_dir.exists():
        logger.warning(f"[{slug}] Diretório não encontrado para limpeza: {output_dir}")
        return

    for f in output_dir.iterdir():
        f.unlink()

    output_dir.rmdir()
    logger.info(f"[{slug}] Imagens deletadas: {output_dir}")
