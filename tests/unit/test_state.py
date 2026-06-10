import json
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from src.state import load_state, save_state, DEFAULT_STATE


def _make_drive_service(state_content: dict | None = None, file_id: str | None = None):
    """Helper que monta um mock do Drive service configurado."""
    service = MagicMock()

    # mock do list de pastas e arquivos
    def list_execute(*args, **kwargs):
        mock = MagicMock()
        if file_id and state_content is not None:
            mock.return_value = {"files": [{"id": file_id}]}
        else:
            mock.return_value = {"files": []}
        return mock

    service.files.return_value.list.return_value.execute.side_effect = None
    service.files.return_value.list.return_value.execute.return_value = {"files": []}
    service.files.return_value.create.return_value.execute.return_value = {"id": "new_folder_id"}

    return service


class TestLoadState:

    def test_retorna_default_state_quando_arquivo_nao_existe(self, empty_state):
        """Deve retornar DEFAULT_STATE quando state.json não existe no Drive."""
        service = MagicMock()
        service.files.return_value.list.return_value.execute.return_value = {"files": []}
        service.files.return_value.create.return_value.execute.return_value = {"id": "folder_id"}

        with patch("src.state._get_service", return_value=service), \
             patch("src.state.os.getenv", return_value="fake_folder_id"):

            result = load_state("one-piece")

        assert result == DEFAULT_STATE

    def test_retorna_state_correto_quando_arquivo_existe(self, populated_state):
        """Deve retornar state correto quando state.json existe no Drive."""
        content = json.dumps(populated_state).encode("utf-8")

        service = MagicMock()
        service.files.return_value.list.return_value.execute.side_effect = [
            {"files": [{"id": "subfolder_id"}]},  # pasta .manga-delivery-state
            {"files": [{"id": "subfolder_id"}]},  # subpasta do slug
            {"files": [{"id": "file_id_123"}]},   # state.json
        ]
        service.files.return_value.create.return_value.execute.return_value = {"id": "new_id"}

        mock_downloader = MagicMock()
        mock_downloader.next_chunk.return_value = (None, True)

        def fake_download(*args, **kwargs):
            args[0].write(content)
            return mock_downloader

        with patch("src.state._get_service", return_value=service), \
             patch("src.state.os.getenv", return_value="fake_folder_id"), \
             patch("src.state.MediaIoBaseDownload", side_effect=fake_download):

            result = load_state("one-piece")

        assert result["last_chapter"] == populated_state["last_chapter"]

    def test_retorna_default_state_em_falha_de_conexao(self):
        """Deve retornar DEFAULT_STATE sem lançar exceção em caso de falha."""
        with patch("src.state._get_service", side_effect=Exception("conexão falhou")):
            result = load_state("one-piece")

        assert result == DEFAULT_STATE

    def test_retorna_default_state_quando_token_invalido(self):
        """Deve retornar DEFAULT_STATE quando token OAuth2 está inválido."""
        with patch("src.state._get_service", side_effect=Exception("token inválido")):
            result = load_state("one-piece")

        assert result == DEFAULT_STATE


class TestSaveState:

    def test_cria_arquivo_quando_nao_existe(self):
        """Deve criar state.json quando não existe no Drive."""
        service = MagicMock()
        service.files.return_value.list.return_value.execute.return_value = {"files": []}
        service.files.return_value.create.return_value.execute.return_value = {"id": "new_id"}

        with patch("src.state._get_service", return_value=service), \
             patch("src.state.os.getenv", return_value="fake_folder_id"):

            save_state("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-1183/")

        service.files.return_value.create.assert_called()

    def test_atualiza_arquivo_quando_existe(self):
        """Deve atualizar state.json quando já existe no Drive."""
        service = MagicMock()
        service.files.return_value.list.return_value.execute.side_effect = [
            {"files": [{"id": "state_folder_id"}]},
            {"files": [{"id": "slug_folder_id"}]},
            {"files": [{"id": "file_id_123"}]},
        ]
        service.files.return_value.update.return_value.execute.return_value = {}

        with patch("src.state._get_service", return_value=service), \
             patch("src.state.os.getenv", return_value="fake_folder_id"):

            save_state("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-1183/")

        service.files.return_value.update.assert_called()

    def test_nao_lanca_excecao_em_falha_de_conexao(self):
        """Deve logar erro sem lançar exceção quando Drive falha."""
        with patch("src.state._get_service", side_effect=Exception("conexão falhou")):
            save_state("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-1183/")

    def test_salva_chapter_url_corretamente(self):
        """State salvo deve conter a URL do capítulo."""
        saved_content = {}

        service = MagicMock()
        service.files.return_value.list.return_value.execute.return_value = {"files": []}
        service.files.return_value.create.return_value.execute.return_value = {"id": "new_id"}

        def capture_upload(fd):
            saved_content["data"] = json.loads(fd.read().decode("utf-8"))
            return MagicMock()

        with patch("src.state._get_service", return_value=service), \
             patch("src.state.os.getenv", return_value="fake_folder_id"), \
             patch("src.state.MediaIoBaseUpload", side_effect=lambda fd, **kw: capture_upload(fd)):

            save_state("one-piece", "https://mangalivre.to/manga/one-piece/capitulo-1183/")

        assert saved_content["data"]["last_chapter"] == "https://mangalivre.to/manga/one-piece/capitulo-1183/"
        assert "last_run" in saved_content["data"]
