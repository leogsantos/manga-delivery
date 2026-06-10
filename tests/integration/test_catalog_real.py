import pytest
from src.catalog import list_available_manga
from src.exceptions import MangaDeliveryError

pytestmark = pytest.mark.integration


class TestCatalogReal:

    def test_retorna_pelo_menos_100_titulos(self):
        """Sitemap real deve ter pelo menos 100 títulos."""
        result = list_available_manga()
        assert len(result) >= 100

    def test_one_piece_esta_na_lista(self):
        """one-piece deve estar na lista de mangás disponíveis."""
        result = list_available_manga()
        slugs = [m["slug"] for m in result]
        assert "one-piece" in slugs

    def test_slugs_nao_contem_url_raiz(self):
        """Nenhum slug deve conter a URL raiz do site."""
        result = list_available_manga()
        for manga in result:
            assert "https://" not in manga["slug"]
            assert manga["slug"] != ""

    def test_todos_tem_slug_e_last_update(self):
        """Todos os itens devem ter slug e last_update preenchidos."""
        try:
            result = list_available_manga()
        except MangaDeliveryError as e:
            if "500" in str(e) or "503" in str(e):
                pytest.skip(f"Site instável: {e}")
            raise

        for manga in result:
            assert manga["slug"]
            assert manga["last_update"]
