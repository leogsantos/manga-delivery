import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

from src.checker import get_latest_chapter
from src.scraper import download_chapter, cleanup_chapter
from src.converter.to_pdf import convert_to_pdf
from src.converter.to_epub import convert_to_epub
from src.storage.gdrive import upload_file
from src.notifier.email import send_chapter_email
from src.state import save_state


def run_single(slug: str) -> None:
    logger.info(f"[{slug}] Iniciando pipeline...")

    # 1. Verifica se há capítulo novo
    chapter = get_latest_chapter(slug)
    if not chapter:
        logger.info(f"[{slug}] Nenhum capítulo novo. Encerrando.")
        return

    chapter_url = chapter["url"]
    chapter_title = chapter["title"]

    # 2. Download das imagens
    image_paths = download_chapter(slug, chapter_url)

    # 3. Conversão
    pdf_path = convert_to_pdf(slug, chapter_url, image_paths)
    epub_path = convert_to_epub(slug, chapter_url, image_paths)

    # 4. Upload Drive (PDF + EPUB)
    drive_link_pdf = upload_file(pdf_path, slug)
    drive_link_epub = upload_file(epub_path, slug)

    # 5. Envia email com EPUB + link do Drive
    send_chapter_email(
        slug=slug,
        chapter_title=chapter_title,
        epub_path=epub_path,
        drive_link=drive_link_epub,
    )

    # 6. Limpa imagens temporárias
    cleanup_chapter(slug, chapter_url)

    # 7. Atualiza state no Drive
    save_state(slug, chapter_url)

    logger.info(f"[{slug}] Pipeline concluído com sucesso.")
    logger.info(f"[{slug}] PDF Drive: {drive_link_pdf}")
    logger.info(f"[{slug}] EPUB Drive: {drive_link_epub}")


def run() -> None:
    raw = os.getenv("MANGA_SLUG", "one-piece")
    slugs = [s.strip() for s in raw.split(",") if s.strip()]

    logger.info(f"Slugs configurados: {slugs}")

    for slug in slugs:
        try:
            run_single(slug)
        except Exception:
            logger.exception(f"[{slug}] Falha no pipeline — continuando para o próximo.")


if __name__ == "__main__":
    run()