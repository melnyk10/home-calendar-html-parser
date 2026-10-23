import logging
import time

import httpx
from bs4 import BeautifulSoup

from src.app.config.settings import settings

logger = logging.getLogger(__name__)

ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5
CHALLENGE_TIMEOUT_MS = 60000
SESSION_NAME = "home-calendar-hltv"


class BlockedError(Exception):
  pass


class FlareSolverrUnavailableError(Exception):
  pass


class HtmlParserService:
  """
  Fetches pages through FlareSolverr, which runs a real browser to pass the
  Cloudflare JS challenge. Plain HTTP clients (cloudscraper, curl_cffi) get 403.
  """

  def __init__(self):
    self._client = httpx.Client(timeout=CHALLENGE_TIMEOUT_MS / 1000 + 30)

  def parse(self, url: str) -> BeautifulSoup:
    for attempt in range(1, ATTEMPTS + 1):
      result = self._get(url)
      if result.get("status") == "ok":
        solution = result["solution"]
        if solution["status"] >= 400:
          raise RuntimeError(f"HTTP {solution['status']} on {url}")
        return BeautifulSoup(solution["response"], "lxml")

      logger.warning(
        f"FlareSolverr failed on {url}: {result.get('message')}, attempt {attempt}/{ATTEMPTS}")
      if attempt < ATTEMPTS:
        time.sleep(RETRY_DELAY_SECONDS)
        # a fresh browser session gets a new challenge instead of reusing the blocked cookies
        self.close_session()

    # the challenge page would parse as a page with no matches, so fail loudly instead
    raise BlockedError(f"Blocked by Cloudflare on {url} after {ATTEMPTS} attempts")

  def _get(self, url: str) -> dict:
    # FlareSolverr creates the session on first use; it keeps the cf_clearance cookie,
    # so only the first request has to solve the challenge
    return self._command(cmd="request.get", url=url, session=SESSION_NAME,
                         maxTimeout=CHALLENGE_TIMEOUT_MS)

  def close_session(self) -> None:
    # an open session keeps Chromium running with the last HLTV page loaded,
    # and its live widgets burn a CPU core until the next sync
    self._command(cmd="sessions.destroy", session=SESSION_NAME)

  def _command(self, **payload) -> dict:
    try:
      return self._client.post(settings.flaresolverr_url, json=payload).json()
    except httpx.ConnectError as e:
      # drop the httpx traceback; the URL is what tells you what's misconfigured
      raise FlareSolverrUnavailableError(
        f"FlareSolverr unreachable at {settings.flaresolverr_url} ({e}). "
        f"Is it running, and is FLARESOLVERR_URL set?") from None
