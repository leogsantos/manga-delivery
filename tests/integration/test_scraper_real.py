import pytest
from src.scraper import download_chapter, cleanup_chapter
from src.checker import get_latest_chapter
from src.state import DEFAULT_STATE

pytestmark = pytest.mark.integration


class TestScraperReal:

    def test_download_capitulo_conhecido(self, tmp_path):
        """Deve baixar imagens de um capítulo real e retornar paths válidos."""
        from unittest.mock import patch
        from playwright._impl._errors import TimeoutError as PlaywrightTimeout

        chapter_url = "https://mangalivre.to/manga/one-piece/capitulo-1183/"

        try:
            with patch("src.scraper.DOWNLOADS_DIR", tmp_path):
                paths = download_chapter("one-piece", chapter_url)
        except Exception as e:
            if "Timeout" in str(e):
                pytest.skip("Playwright timeout — rede lenta ou site instável")
            raise

        assert len(paths) > 0
        assert all(p.exists() for p in paths)
        assert all(p.suffix == ".webp" for p in paths)

        with patch("src.scraper.DOWNLOADS_DIR", tmp_path):
            cleanup_chapter("one-piece", chapter_url)

    def test_numero_de_imagens_condizente(self, tmp_path):
        """Capítulo real deve ter entre 10 e 30 imagens."""
        from unittest.mock import patch

        chapter_url = "https://mangalivre.to/manga/one-piece/capitulo-1183/"

        with patch("src.scraper.DOWNLOADS_DIR", tmp_path):
            paths = download_chapter("one-piece", chapter_url)
            cleanup_chapter("one-piece", chapter_url)

        assert 10 <= len(paths) <= 30
