from io import BytesIO
from pathlib import Path

from PIL import Image

from src.exceptions import MangaDeliveryError


class ImageConversionError(MangaDeliveryError):
    """Falha ao converter imagem."""


def webp_to_jpeg_bytes(path: Path, max_width: int = 1200) -> bytes:
    try:
        with Image.open(path) as img:
            rgb = img.convert("RGB")
            if rgb.width > max_width:
                ratio = max_width / rgb.width
                new_height = int(rgb.height * ratio)
                rgb = rgb.resize((max_width, new_height), Image.LANCZOS)
            buffer = BytesIO()
            rgb.save(buffer, format="JPEG", quality=75)
            return buffer.getvalue()
    except Exception as e:
        raise ImageConversionError(f"Falha ao converter '{path.name}' para JPEG: {e}") from e