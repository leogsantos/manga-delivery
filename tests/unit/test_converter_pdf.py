import pytest
from pathlib import Path
from unittest.mock import patch
from src.converter.to_pdf import convert_to_pdf, PdfConversionError


class TestConvertToPdf:

    def test_gera_pdf_no_caminho_correto(self, sample_image_list, tmp_path):
        """Deve gerar PDF no diretório output/{slug}/."""
        with patch("src.converter.to_pdf.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            pdf_path = convert_to_pdf(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=sample_image_list,
            )

        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"
        assert pdf_path.parent.name == "one-piece"
        assert "capitulo-1183" in pdf_path.name

    def test_pdf_tem_conteudo(self, sample_image_list, tmp_path):
        """PDF gerado deve ter conteúdo (não estar vazio)."""
        with patch("src.converter.to_pdf.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            pdf_path = convert_to_pdf(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=sample_image_list,
            )

        assert pdf_path.stat().st_size > 0

    def test_lanca_pdf_conversion_error_com_imagem_corrompida(self, tmp_path):
        """Deve lançar PdfConversionError quando imagem está corrompida."""
        imagem_corrompida = tmp_path / "001.webp"
        imagem_corrompida.write_bytes(b"bytes_invalidos_nao_sao_imagem")

        with patch("src.converter.to_pdf.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            with pytest.raises(PdfConversionError):
                convert_to_pdf(
                    slug="one-piece",
                    chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                    image_paths=[imagem_corrompida],
                )

    def test_nome_do_arquivo_contem_slug_e_capitulo(self, sample_image_list, tmp_path):
        """Nome do PDF deve conter o slug e o número do capítulo."""
        with patch("src.converter.to_pdf.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            pdf_path = convert_to_pdf(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=sample_image_list,
            )

        assert "one-piece" in pdf_path.name
        assert "1183" in pdf_path.name

    def test_aceita_lista_de_uma_imagem(self, sample_webp_image, tmp_path):
        """Deve funcionar com apenas uma imagem."""
        with patch("src.converter.to_pdf.OUTPUT_DIR", tmp_path), \
             patch("src.scraper.DOWNLOADS_DIR", tmp_path):

            pdf_path = convert_to_pdf(
                slug="one-piece",
                chapter_url="https://mangalivre.to/manga/one-piece/capitulo-1183/",
                image_paths=[sample_webp_image],
            )

        assert pdf_path.exists()
