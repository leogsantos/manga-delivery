import pytest
from src.checker import get_latest_chapter
from src.exceptions import PageFetchError, NonceMissingError, ChapterParseError
from src.state import DEFAULT_STATE

pytestmark = pytest.mark.integration


class TestCheckerReal:

    def test_slug_valido_retorna_capitulo_ou_none(self):
        """
        Com slug válido deve retornar dict com title/url/date
        ou None se não houver capítulo novo.
        """
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("src.checker.load_state", lambda slug: DEFAULT_STATE)
            result = get_latest_chapter("one-piece")

        if result is not None:
            assert "title" in result
            assert "url" in result
            assert "date" in result
            assert "capitulo" in result["url"].lower()

    def test_slug_inexistente_lanca_excecao(self):
        """
        Slug inexistente deve lançar PageFetchError, NonceMissingError
        ou ChapterParseError — nunca retornar silenciosamente.
        """
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("src.checker.load_state", lambda slug: DEFAULT_STATE)
            with pytest.raises((PageFetchError, NonceMissingError, ChapterParseError)):
                get_latest_chapter("slug-que-nao-existe-xyz-404-abc")

    def test_pipeline_nao_quebra_silenciosamente_com_slug_invalido(self):
        """
        Com slug inválido o pipeline deve lançar exceção conhecida,
        nunca retornar None silenciosamente como se fosse 'sem capítulo novo'.
        """
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("src.checker.load_state", lambda slug: DEFAULT_STATE)
            raised = False
            try:
                get_latest_chapter("manga-inexistente-9999")
            except (PageFetchError, NonceMissingError, ChapterParseError):
                raised = True
            except Exception as e:
                pytest.fail(f"Exceção inesperada lançada: {type(e).__name__}: {e}")

        assert raised, "Slug inválido retornou None silenciosamente — deveria lançar exceção"
