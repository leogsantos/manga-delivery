import pytest
from unittest.mock import patch
from src.catalog import list_available_manga, print_catalog
from src.exceptions import MangaDeliveryError, BotBlockedError


class TestListAvailableManga:

    def test_retorna_lista_de_mangas(self, sitemap_xml, mock_httpx_response):
        """Deve retornar lista de mangás extraída do sitemap."""
        response = mock_httpx_response(status_code=200, text=sitemap_xml)
        with patch("src.catalog.httpx.get", return_value=response):
            result = list_available_manga()

        assert isinstance(result, list)
        assert len(result) == 2  # exclui a URL raiz
        slugs = [m["slug"] for m in result]
        assert "one-piece" in slugs
        assert "chainsaw-man-pt-br" in slugs

    def test_filtra_url_raiz_do_sitemap(self, sitemap_xml, mock_httpx_response):
        """Não deve incluir a URL raiz https://mangalivre.to/manga/ na lista."""
        response = mock_httpx_response(status_code=200, text=sitemap_xml)
        with patch("src.catalog.httpx.get", return_value=response):
            result = list_available_manga()

        slugs = [m["slug"] for m in result]
        assert "https://mangalivre.to/manga" not in slugs
        assert "" not in slugs

    def test_retorna_ordenado_por_data_decrescente(self, sitemap_xml, mock_httpx_response):
        """Deve retornar lista ordenada pela data de atualização mais recente primeiro."""
        response = mock_httpx_response(status_code=200, text=sitemap_xml)
        with patch("src.catalog.httpx.get", return_value=response):
            result = list_available_manga()

        datas = [m["last_update"] for m in result if m["last_update"]]
        assert datas == sorted(datas, reverse=True)

    def test_lanca_bot_blocked_error_no_418(self, mock_httpx_response):
        """Deve lançar BotBlockedError quando site retorna 418."""
        response = mock_httpx_response(status_code=418)
        with patch("src.catalog.httpx.get", return_value=response):
            with pytest.raises(BotBlockedError):
                list_available_manga()

    def test_lanca_manga_delivery_error_em_falha_http(self, mock_httpx_response):
        """Deve lançar MangaDeliveryError quando site retorna erro HTTP."""
        import httpx
        with patch("src.catalog.httpx.get", side_effect=httpx.HTTPError("timeout")):
            with pytest.raises(MangaDeliveryError):
                list_available_manga()

    def test_cada_manga_tem_slug_e_last_update(self, sitemap_xml, mock_httpx_response):
        """Cada item da lista deve ter as chaves slug e last_update."""
        response = mock_httpx_response(status_code=200, text=sitemap_xml)
        with patch("src.catalog.httpx.get", return_value=response):
            result = list_available_manga()

        for manga in result:
            assert "slug" in manga
            assert "last_update" in manga


class TestPrintCatalog:

    def test_imprime_sem_erros(self, sitemap_xml, mock_httpx_response, capsys):
        """Deve imprimir o catálogo sem lançar exceções."""
        response = mock_httpx_response(status_code=200, text=sitemap_xml)
        with patch("src.catalog.httpx.get", return_value=response):
            print_catalog()

        captured = capsys.readouterr()
        assert "one-piece" in captured.out
        assert "Total:" in captured.out

    def test_exibe_total_correto(self, sitemap_xml, mock_httpx_response, capsys):
        """Deve exibir o total correto de títulos."""
        response = mock_httpx_response(status_code=200, text=sitemap_xml)
        with patch("src.catalog.httpx.get", return_value=response):
            print_catalog()

        captured = capsys.readouterr()
        assert "Total: 2 títulos" in captured.out
