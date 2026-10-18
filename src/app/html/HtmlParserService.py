import logging
import time

import cloudscraper
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5


class BlockedError(Exception):
  pass


class HtmlParserService:
  def __init__(self):
    self._scraper = cloudscraper.create_scraper()

  def parse(self, url: str) -> BeautifulSoup:
    for attempt in range(1, ATTEMPTS + 1):
      response = self._scraper.get(url, timeout=30)
      if not self._is_blocked(response):
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

      logger.warning(
        f"Blocked by Cloudflare ({response.status_code}) on {url}, attempt {attempt}/{ATTEMPTS}")
      if attempt < ATTEMPTS:
        time.sleep(RETRY_DELAY_SECONDS)
        # a fresh session gets a new challenge instead of reusing the blocked cookies
        self._scraper = cloudscraper.create_scraper()

    # the challenge page would parse as a page with no matches, so fail loudly instead
    raise BlockedError(f"Blocked by Cloudflare on {url} after {ATTEMPTS} attempts")

  @staticmethod
  def _is_blocked(response) -> bool:
    return response.status_code in (403, 503) and "just a moment" in response.text.lower()
