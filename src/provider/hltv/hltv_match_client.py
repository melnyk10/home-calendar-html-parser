import logging
import re
from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

from src.common.consts import HEADERS
from src.provider.hltv.dto.HltvMatchResponse import HltvMatchResponse
from src.provider.hltv.dto.HltvStream import HltvStream

logger = logging.getLogger(__name__)


class HltvMatchesClient:
  BASE_URL = "https://www.hltv.org"

  async def sync_matches(self, team_id: int, slug: str) -> List[
    HltvMatchResponse]:
    """
    Fetch recent match results for a specific HLTV team.
    """
    url = f"{self.BASE_URL}/team/{team_id}/{slug}"
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
      response = await client.get(url)
      response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    matches = await self.parse_match_table(soup)
    return matches

  async def parse_match_table(self, soup) -> List[HltvMatchResponse]:
    # todo: parse only first tournament
    match_table = soup.select_one("table.match-table")
    if not match_table:
      return []

    current_event_name = None
    current_event_url = None

    matches = []
    for tr in match_table.select("tr"):
      try:
        class_list = tr.get("class", [])

        if "event-header-cell" in class_list:
          a = tr.select_one("a.a-reset")
          if a:
            current_event_name = a.text.strip()
            current_event_url = f"{self.BASE_URL}{a['href']}"

        elif "team-row" in class_list:
          try:
            match = self._parse_match_row(tr)
            if match:
              match.event_name = current_event_name
              match.event_url = current_event_url
              await self._enrich_match_details(match)
              matches.append(match)
          except Exception as e:
            logger.warning(f"Failed to parse match row: {e}")
      except Exception as e:
        logger.warning(f"Failed to parse match row: {e}")

    return matches

  def _parse_match_row(self, tr) -> Optional[HltvMatchResponse]:
    try:
      date_span = tr.select_one("td.date-cell span")
      timestamp = int(date_span.get("data-unix")) // 1000
      match_datetime = datetime.fromtimestamp(timestamp)

      team_names = tr.select("td.team-center-cell a.team-name")

      team1 = team_names[0].text.strip() if len(
        team_names) > 0 else None  # todo: is it possible that team1 can be TBD ?
      team2 = team_names[1].text.strip() if len(
        team_names) > 1 else None  # todo: is it possible that team1 can be TBD ?

      scores = tr.select("div.score-cell span.score")
      score1 = int(scores[0].text.strip()) if len(scores) > 0 and scores[
        0].text.strip().isdigit() else None
      score2 = int(scores[1].text.strip()) if len(scores) > 1 and scores[
        1].text.strip().isdigit() else None

      match_url = None
      match_id = None

      link = tr.select_one("td.matchpage-button-cell a.matchpage-button")
      if link and link.has_attr("href"):
        match_url = f"{self.BASE_URL}{link['href']}"
        match_id_match = re.search(r"/matches/(\d+)", link["href"])
        match_id = int(match_id_match.group(1)) if match_id_match else 0

      return HltvMatchResponse(
        match_id=match_id,
        match_url=match_url,
        datetime=match_datetime,
        team1=team1,
        team2=team2,
        score1=score1,
        score2=score2,
      )
    except Exception as e:
      logger.error(f"Error parsing row: {e}")
      return None

  async def _enrich_match_details(self, match: HltvMatchResponse):
    if not match.match_url:
      return

    HEADERS = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
      ),
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
      "Accept-Encoding": "gzip, deflate, br",
      "Referer": "https://www.hltv.org/",
    }

    try:
      async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        response = await client.get(match.match_url)
        response.raise_for_status()
        html = response.text  # <--- Correct! Will decode gzip/br
        soup = BeautifulSoup(html, "lxml")

      best_of_text = soup.find(string=re.compile(r"Best of \d+"))
      if best_of_text:
        match.best_of = int(re.search(r"Best of (\d+)", best_of_text).group(1))

      match.streams = self._extract_streams(soup)

    except Exception as e:
      logger.warning(f"Failed to enrich match {match.match_id}: {e}")

  def _extract_streams(self, soup: BeautifulSoup) -> List[HltvStream]:
    streams = []

    for stream_box in soup.select(".stream-box"):
      embed = stream_box.select_one(".stream-box-embed[data-stream-embed]")
      if not embed:
        continue

      url = embed.get("data-stream-embed")

      img = embed.find("img")
      flag_title = img.get("title") if img else None

      name = None
      for child in embed.children:
        if getattr(child, "name", None) == "img":
          next_text = child.next_sibling
          if next_text and isinstance(next_text, str):
            name = next_text.strip()
          break

      viewers_span = stream_box.select_one(
        ".watchbox-right .viewers.gtSmartphone-only")
      viewers = int(viewers_span.text.strip().replace(",",
                                                      "")) if viewers_span and viewers_span.text.strip().isdigit() else None

      if url and name:
        streams.append(HltvStream(
          name=name,
          url=url,
          flag_title=flag_title,
          viewers=viewers
        ))

    return streams
