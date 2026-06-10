class MangaDeliveryError(Exception):
    """Base do projeto."""

class PageFetchError(MangaDeliveryError):
    """Falha ao buscar página do mangá."""

class NonceMissingError(MangaDeliveryError):
    """Não encontrou manga_id ou nonce no HTML."""

class ChapterFetchError(MangaDeliveryError):
    """Falha na chamada AJAX de capítulos."""

class ChapterParseError(MangaDeliveryError):
    """Falha ao parsear HTML dos capítulos."""

class BotBlockedError(MangaDeliveryError):
    """Site bloqueou a requisição por ausência ou invalidade do User-Agent."""