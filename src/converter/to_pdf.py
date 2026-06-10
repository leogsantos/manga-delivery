import logging
from io import BytesIO
from pathlib import Path

import img2pdf
from PIL import Image

from src.exceptions import MangaDeliveryError
from src.converter import webp_to_jpeg_bytes

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")


class PdfConversionError(MangaDeliveryError):
    """Falha ao converter imagens para PDF."""



def convert_to_pdf(slug: str, chapter_url: str, image_paths: list[Path]) -> Path:
    """
    Converte lista de imagens webp em um PDF único.
    Retorna o path do PDF gerado.
    """
    from src.scraper import _resolve_output_dir  # evita import circular no topo

    chapter_id = _resolve_output_dir(slug, chapter_url).name  # ex: capitulo-1183
    output_dir = OUTPUT_DIR / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / f"{slug}-{chapter_id}.pdf"

    logger.info(f"[{slug}] Convertendo {len(image_paths)} imagens para PDF...")

    try:
        jpeg_images = [webp_to_jpeg_bytes(p) for p in sorted(image_paths)]
        pdf_bytes = img2pdf.convert(jpeg_images)
        pdf_path.write_bytes(pdf_bytes)
    except PdfConversionError:
        raise
    except Exception as e:
        raise PdfConversionError(f"Falha ao gerar PDF para '{slug}' {chapter_id}: {e}") from e

    logger.info(f"[{slug}] PDF gerado: {pdf_path}")
    return pdf_path