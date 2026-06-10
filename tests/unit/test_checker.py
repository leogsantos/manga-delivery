import pytest
from unittest.mock import patch, MagicMock
from src.checker import get_latest_chapter, _extract_page_meta, _fetch_chapters
from src.exceptions import (
    BotBlockedError,
    PageFetchError,
    NonceMissingError,
    ChapterFetchError,
    ChapterParseError,
)


class TestExtractPageMeta:

    def test_extrai_manga_id_e_nonce_corretamente(self, manga_page_html, mock_httpx_response):
        """Deve extrair manga_id e nonce do HTML da página."""
        response = mock_httpx_response(status_code=200, text=manga_page_html)
        with patch("src.checker.httpx.get", return_value=response):
            manga_id, nonce = _extract_page_meta("one-piece")

        assert manga_id == "12345"
        assert nonce == "abc123def456"

    def test_lanca_bot_blocked_error_no_418(self, mock_httpx_response):
        """Deve lançar BotBlockedError quando site retorna 418."""
        response = mock_httpx_response(status_code=418)
        with patch("src.checker.httpx.get", return_value=response):
            with pytest.raises(BotBlockedError):
                _extract_page_meta("one-piece")

    def test_lanca_page_fetch_error_em_falha_http(self):
        """Deve lançar PageFetchError em falha de conexão."""
        import httpx
        with patch("src.checker.httpx.get", side_effect=httpx.HTTPError("timeout")):
            with pytest.raises(PageFetchError):
                _extract_page_meta("one-piece")

    def test_lanca_nonce_missing_error_quando_nao_encontrado(self, mock_httpx_response):
        """Deve lançar NonceMissingError quando manga_id ou nonce não está no HTML."""
        response = mock_httpx_response(status_code=200, text="<html><body>sem dados</body></html>")
        with patch("src.checker.httpx.get", return_value=response):
            with pytest.raises(NonceMissingError):
                _extract_page_meta("one-piece")


class TestFetchChapters:

    def test_retorna_lista_de_capitulos(self, chapter_list_html, mock_httpx_response):
        """Deve retornar lista de capítulos parseada corretamente."""
        response = mock_httpx_response(status_code=200, text=chapter_list_html)
        with patch("src.checker.httpx.post", return_value=response):
            chapters = _fetch_chapters("one-piece", "12345", "abc123")

        assert len(chapters) == 2
        assert chapters[0]["title"] == "Capitulo 1183"
        assert chapters[0]["url"] == "https://mangalivre.to/manga/one-piece/capitulo-1183/"
        assert chapters[0]["date"] == "maio 28, 2026"

    def test_lanca_bot_blocked_error_no_418(self, mock_httpx_response):
        """Deve lançar BotBlockedError quando AJAX retorna 418."""
        response = mock_httpx_response(status_code=418)
        with patch("src.checker.httpx.post", return_value=response):
            with pytest.raises(BotBlockedError):
                _fetch_chapters("one-piece", "12345", "abc123")

    def test_lanca_chapter_fetch_error_em_falha_http(self):
        """Deve lançar ChapterFetchError em falha de conexão."""
        import httpx
        with patch("src.checker.httpx.post", side_effect=httpx.HTTPError("timeout")):
            with pytest.raises(ChapterFetchError):
                _fetch_chapters("one-piece", "12345", "abc123")

    def test_retorna_lista_vazia_quando_sem_capitulos(self, mock_httpx_response):
        """Deve retornar lista vazia quando HTML não tem capítulos."""
        response = mock_httpx_response(status_code=200, text="<ul></ul>")
        with patch("src.checker.httpx.post", return_value=response):
            chapters = _fetch_chapters("one-piece", "12345", "abc123")

        assert chapters == []


class TestGetLatestChapter:

    def test_retorna_capitulo_quando_novo(
        self, manga_page_html, chapter_list_html, mock_httpx_response, empty_state
    ):
        """Deve retornar capítulo quando é diferente do state."""
        page_response = mock_httpx_response(status_code=200, text=manga_page_html)
        chapters_response = mock_httpx_response(status_code=200, text=chapter_list_html)

        with patch("src.checker.httpx.get", return_value=page_response), \
             patch("src.checker.httpx.post", return_value=chapters_response), \
             patch("src.checker.load_state", return_value=empty_state):

            result = get_latest_chapter("one-piece")

        assert result is not None
        assert result["title"] == "Capitulo 1183"

    def test_retorna_none_quando_sem_capitulo_novo(
        self, manga_page_html, chapter_list_html, mock_httpx_response, populated_state
    ):
        """Deve retornar None quando capítulo já foi processado."""
        page_response = mock_httpx_response(status_code=200, text=manga_page_html)
        chapters_response = mock_httpx_response(status_code=200, text=chapter_list_html)

        with patch("src.checker.httpx.get", return_value=page_response), \
             patch("src.checker.httpx.post", return_value=chapters_response), \
             patch("src.checker.load_state", return_value=populated_state):

            result = get_latest_chapter("one-piece")

        assert result is None

    def test_retorna_none_quando_lista_de_capitulos_vazia(
        self, manga_page_html, mock_httpx_response, empty_state
    ):
        """Deve retornar None quando não há capítulos na lista."""
        page_response = mock_httpx_response(status_code=200, text=manga_page_html)
        empty_response = mock_httpx_response(status_code=200, text="<ul></ul>")

        with patch("src.checker.httpx.get", return_value=page_response), \
             patch("src.checker.httpx.post", return_value=empty_response), \
             patch("src.checker.load_state", return_value=empty_state):

            result = get_latest_chapter("one-piece")

        assert result is None

    def test_propaga_excecao_de_pagina_nao_encontrada(self, mock_httpx_response):
        """Deve propagar PageFetchError quando página não existe."""
        import httpx
        with patch("src.checker.httpx.get", side_effect=httpx.HTTPError("404")):
            with pytest.raises(PageFetchError):
                get_latest_chapter("slug-inexistente-xyz-404")
