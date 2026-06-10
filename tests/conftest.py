import pytest
from pathlib import Path
from unittest.mock import MagicMock


# ── HTML fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def manga_page_html():
    """HTML simulado da página de um mangá com manga_id e nonce válidos."""
    return """
    <html>
    <head></head>
    <body>
    <script>
        var manga_id = "12345";
        var nonce = "abc123def456";
        var manga_data = {"manga_id": "12345", "nonce": "abc123def456"};
    </script>
    </body>
    </html>
    """


@pytest.fixture
def chapter_list_html():
    """HTML simulado retornado pela Madara AJAX API com lista de capítulos."""
    return """
    <ul>
        <li class="wp-manga-chapter">
            <a href="https://mangalivre.to/manga/one-piece/capitulo-1183/">Capitulo 1183</a>
            <span class="chapter-release-date"><i>maio 28, 2026</i></span>
        </li>
        <li class="wp-manga-chapter">
            <a href="https://mangalivre.to/manga/one-piece/capitulo-1182/">Capitulo 1182</a>
            <span class="chapter-release-date"><i>maio 21, 2026</i></span>
        </li>
    </ul>
    """


@pytest.fixture
def chapter_page_html():
    """HTML simulado da página de um capítulo com imagens carregadas."""
    return """
    <html>
    <body>
        <img id="image-0" class="wp-manga-chapter-img" src=" https://mangalivre.to/wp-content/uploads/WP-manga/data/manga_123/hash/001.webp"/>
        <img id="image-1" class="wp-manga-chapter-img" src=" https://mangalivre.to/wp-content/uploads/WP-manga/data/manga_123/hash/002.webp"/>
        <img id="image-2" class="wp-manga-chapter-img" src=" https://mangalivre.to/wp-content/uploads/WP-manga/data/manga_123/hash/003.webp"/>
    </body>
    </html>
    """


@pytest.fixture
def sitemap_xml():
    """XML simulado do sitemap de mangás."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://mangalivre.to/manga/</loc>
            <lastmod>2026-05-28T09:51:36+00:00</lastmod>
        </url>
        <url>
            <loc>https://mangalivre.to/manga/one-piece/</loc>
            <lastmod>2026-03-05T23:09:20+00:00</lastmod>
        </url>
        <url>
            <loc>https://mangalivre.to/manga/chainsaw-man-pt-br/</loc>
            <lastmod>2026-05-28T09:51:36+00:00</lastmod>
        </url>
    </urlset>
    """


# ── State fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def empty_state():
    """State padrão sem capítulo processado."""
    return {"last_chapter": None, "last_run": None}


@pytest.fixture
def populated_state():
    """State com capítulo já processado."""
    return {
        "last_chapter": "https://mangalivre.to/manga/one-piece/capitulo-1183/",
        "last_run": "2026-05-28T12:00:00+00:00",
    }


# ── Image fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_webp_image(tmp_path) -> Path:
    """Cria uma imagem webp válida de 100x100px para testes."""
    from PIL import Image
    img_path = tmp_path / "001.webp"
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    img.save(img_path, format="WEBP")
    return img_path


@pytest.fixture
def sample_image_list(tmp_path) -> list[Path]:
    """Cria uma lista de 3 imagens webp válidas para testes de conversão."""
    from PIL import Image
    paths = []
    for i in range(1, 4):
        img_path = tmp_path / f"{str(i).zfill(3)}.webp"
        img = Image.new("RGB", (800, 1200), color=(i * 80, i * 80, i * 80))
        img.save(img_path, format="WEBP")
        paths.append(img_path)
    return paths


# ── HTTP mock helpers ────────────────────────────────────────────────────────

@pytest.fixture
def mock_httpx_response():
    """Factory de respostas HTTP mockadas."""
    def _make_response(status_code: int = 200, text: str = "", content: bytes = b""):
        response = MagicMock()
        response.status_code = status_code
        response.text = text
        response.content = content
        response.raise_for_status = MagicMock()
        if status_code >= 400:
            import httpx
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message=f"HTTP {status_code}",
                request=MagicMock(),
                response=response,
            )
        return response
    return _make_response


# ── Drive mock ───────────────────────────────────────────────────────────────

@pytest.fixture
def mock_drive_service():
    """Mock do client do Google Drive."""
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {"files": []}
    service.files.return_value.create.return_value.execute.return_value = {
        "id": "fake_file_id_123",
        "webViewLink": "https://drive.google.com/file/d/fake_file_id_123/view",
    }
    service.files.return_value.update.return_value.execute.return_value = {}
    return service
