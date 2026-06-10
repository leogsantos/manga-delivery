import time
import functools
import logging

logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3, base_delay: float = 2.0, exceptions: tuple = (Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    delay = base_delay ** attempt
                    logger.warning(f"[{func.__name__}] Tentativa {attempt} falhou: {e}. Retry em {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}