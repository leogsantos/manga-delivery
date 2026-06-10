import logging
from io import BytesIO
from pathlib import Path

from ebooklib import epub
from PIL import Image

from src.exceptions import MangaDeliveryError
from src.converter import webp_to_jpeg_bytes

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")


class EpubConversionError(MangaDeliveryError):
    """Falha ao converter imagens para EPUB."""


def _build_image_page(index: int, image_name: str) -> epub.EpubHtml:
    page = epub.EpubHtml(
        title=f"Página {index + 1}",
        file_name=f"page_{str(index + 1).zfill(3)}.xhtml",
        lang="pt",
    )
    page.content = f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Página {index + 1}</title>
    <style>
        body {{ margin: 0; padding: 0; background: #000; }}
        img {{ width: 100%; height: auto; display: block; }}
    </style>
</head>
<body>
    <img src="images/{image_name}" alt="Página {index + 1}"/>
</body>
</html>""".encode("utf-8")
    return page


def convert_to_epub(slug: str, chapter_url: str, image_paths: list[Path]) -> Path:
    """
    Converte lista de imagens webp em EPUB.
    Retorna o path do EPUB gerado.
    """
    from src.scraper import _resolve_output_dir

    chapter_id = _resolve_output_dir(slug, chapter_url).name  # ex: capitulo-1183
    output_dir = OUTPUT_DIR / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    epub_path = output_dir / f"{slug}-{chapter_id}.epub"

    logger.info(f"[{slug}] Gerando EPUB com {len(image_paths)} imagens...")

    try:
        book = epub.EpubBook()
        book.set_identifier(f"{slug}-{chapter_id}")
        book.set_title(f"{slug.replace('-', ' ').title()} — {chapter_id.replace('-', ' ').title()}")
        book.set_language("pt")
        book.add_author("manga-delivery")

        pages = []

        for i, path in enumerate(sorted(image_paths)):
            jpeg_bytes = webp_to_jpeg_bytes(path)
            image_name = f"{str(i + 1).zfill(3)}.jpeg"

            epub_image = epub.EpubImage(
                uid=f"image_{i}",
                file_name=f"images/{image_name}",
                media_type="image/jpeg",
                content=jpeg_bytes,
            )
            book.add_item(epub_image)

            page = _build_image_page(i, image_name)
            book.add_item(page)
            pages.append(page)

        book.toc = tuple(pages)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav"] + pages

        epub.write_epub(str(epub_path), book)

    except EpubConversionError:
        raise
    except Exception as e:
        raise EpubConversionError(f"Falha ao gerar EPUB para '{slug}' {chapter_id}: {e}") from e

    logger.info(f"[{slug}] EPUB gerado: {epub_path}")
    return epub_path