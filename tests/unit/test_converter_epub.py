import pytest
import zipfile
from pathlib import Path
from unittest.mock import patch
from src.converter.to_epub import convert_to_epub, EpubConversionError


class TestConvertToEpub:

    def test_gera_epub_no_caminho_correto(self, sample_image_list, tmp_path):
        """Deve gerar EPUB no diretório output/{slug}/."""
        with patch("src.converter.to_epub.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            epub_path = convert_to_epub(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=sample_image_list,
            )

        assert epub_path.exists()
        assert epub_path.suffix == ".epub"
        assert epub_path.parent.name == "one-piece"
        assert "capitulo-1183" in epub_path.name

    def test_epub_tem_conteudo(self, sample_image_list, tmp_path):
        """EPUB gerado deve ter conteúdo (não estar vazio)."""
        with patch("src.converter.to_epub.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            epub_path = convert_to_epub(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=sample_image_list,
            )

        assert epub_path.stat().st_size > 0

    def test_epub_e_zip_valido(self, sample_image_list, tmp_path):
        """EPUB deve ser um arquivo ZIP válido (formato padrão do EPUB)."""
        with patch("src.converter.to_epub.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            epub_path = convert_to_epub(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=sample_image_list,
            )

        assert zipfile.is_zipfile(epub_path)

    def test_epub_contem_imagens(self, sample_image_list, tmp_path):
        """EPUB deve conter as imagens convertidas para JPEG."""
        with patch("src.converter.to_epub.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            epub_path = convert_to_epub(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=sample_image_list,
            )

        with zipfile.ZipFile(epub_path) as z:
            names = z.namelist()
            jpeg_files = [n for n in names if n.endswith(".jpeg")]

        assert len(jpeg_files) == len(sample_image_list)

    def test_epub_contem_paginas_html(self, sample_image_list, tmp_path):
        """EPUB deve conter páginas HTML para cada imagem."""
        with patch("src.converter.to_epub.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            epub_path = convert_to_epub(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=sample_image_list,
            )

        with zipfile.ZipFile(epub_path) as z:
            names = z.namelist()
            xhtml_files = [n for n in names if n.endswith(".xhtml")]

        assert len(xhtml_files) >= len(sample_image_list)

    def test_lanca_epub_conversion_error_com_imagem_corrompida(self, tmp_path):
        """Deve lançar EpubConversionError quando imagem está corrompida."""
        imagem_corrompida = tmp_path / "001.webp"
        imagem_corrompida.write_bytes(b"bytes_invalidos_nao_sao_imagem")

        with patch("src.converter.to_epub.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            with pytest.raises(EpubConversionError):
                convert_to_epub(
                    slug="one-piece",
                    chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                    image_paths=[imagem_corrompida],
                )

    def test_nome_do_arquivo_contem_slug_e_capitulo(self, sample_image_list, tmp_path):
        """Nome do EPUB deve conter o slug e o número do capítulo."""
        with patch("src.converter.to_epub.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            epub_path = convert_to_epub(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=sample_image_list,
            )

        assert "one-piece" in epub_path.name
        assert "1183" in epub_path.name
