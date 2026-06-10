import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from src.scraper import (
    _extract_image_urls,
    _resolve_output_dir,
    download_chapter,
    cleanup_chapter,
)
from src.exceptions import BotBlockedError, PageFetchError, ChapterParseError


class TestExtractImageUrls:

    def test_extrai_urls_corretamente(self, chapter_page_html):
        """Deve extrair URLs das imagens da classe wp-manga-chapter-img."""
        urls = _extract_image_urls(chapter_page_html, "https://mangalivre.to/manga/one-piece/capitulo-1183/")

        assert len(urls) == 3
        assert all("WP-manga/data" in url for url in urls)
        assert all(url.endswith(".webp") for url in urls)

    def test_remove_espaco_do_src(self, chapter_page_html):
        """Deve remover o espaço no início do atributo src."""
        urls = _extract_image_urls(chapter_page_html, "https://mangalivre.to/manga/one-piece/capitulo-1183/")

        for url in urls:
            assert not url.startswith(" ")

    def test_lanca_chapter_parse_error_sem_imagens(self):
        """Deve lançar ChapterParseError quando não há imagens na página."""
        html = "<html><body><p>sem imagens</p></body></html>"
        with pytest.raises(ChapterParseError):
            _extract_image_urls(html, "https://mangalivre.to/manga/one-piece/capitulo-1183/")

    def test_lanca_chapter_parse_error_com_lista_vazia(self):
        """Deve lançar ChapterParseError quando imgs existem mas sem src."""
        html = '<html><body><img class="wp-manga-chapter-img"/></body></html>'
        with pytest.raises(ChapterParseError):
            _extract_image_urls(html, "https://mangalivre.to/manga/one-piece/capitulo-1183/")


class TestResolveOutputDir:

    def test_resolve_capitulo_simples(self, tmp_path):
        """Deve criar diretório correto para capítulo simples."""
        with patch("src.scraper.DOWNLOADS_DIR", tmp_path):
            output_dir = _resolve_output_dir("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-1183/")

        assert output_dir.name == "capitulo-1183"
        assert output_dir.parent.name == "one-piece"
        assert output_dir.exists()

    def test_resolve_capitulo_decimal(self, tmp_path):
        """Deve lidar com capítulos decimais como capitulo-196-1."""
        with patch("src.scraper.DOWNLOADS_DIR", tmp_path):
            output_dir = _resolve_output_dir("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-196-1/")

        assert output_dir.name == "capitulo-196-1"

    def test_usa_desconhecido_quando_url_invalida(self, tmp_path):
        """Deve usar 'desconhecido' quando não consegue extrair o número."""
        with patch("src.scraper.DOWNLOADS_DIR", tmp_path):
            output_dir = _resolve_output_dir("one-piece", "https://mangalivre.to/manga/one-piece/")

        assert output_dir.name == "capitulo-desconhecido"


class TestDownloadChapter:

    def test_retorna_lista_de_paths_ordenada(self, chapter_page_html, tmp_path):
        """Deve retornar lista de paths ordenada após download."""
        fake_image_bytes = b"fake_image_content"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.content = fake_image_bytes

        async def mock_get(*args, **kwargs):
            return mock_response

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = mock_get

        with patch("src.scraper._fetch_chapter_html", return_value=chapter_page_html), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path), \
             patch("src.scraper.httpx.AsyncClient", return_value=mock_client):

            paths = download_chapter("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-1183/")

        assert len(paths) == 3
        assert all(isinstance(p, Path) for p in paths)
        assert paths == sorted(paths)

    def test_lanca_page_fetch_error_quando_playwright_falha(self):
        """Deve lançar PageFetchError quando Playwright não consegue renderizar."""
        with patch("src.scraper._fetch_chapter_html", side_effect=PageFetchError("falha")):
            with pytest.raises(PageFetchError):
                download_chapter("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-1183/")


class TestCleanupChapter:

    def test_deleta_imagens_e_pasta(self, tmp_path):
        """Deve deletar todas as imagens e a pasta do capítulo."""
        with patch("src.scraper.DOWNLOADS_DIR", tmp_path):
            output_dir = _resolve_output_dir("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-1183/")
            (output_dir / "001.webp").write_bytes(b"fake")
            (output_dir / "002.webp").write_bytes(b"fake")

            cleanup_chapter("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-1183/")

        assert not output_dir.exists()

    def test_nao_lanca_erro_quando_pasta_inexistente(self, tmp_path):
        """Deve logar warning sem lançar exceção quando pasta não existe."""
        with patch("src.scraper.DOWNLOADS_DIR", tmp_path):
            cleanup_chapter("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-9999/")
