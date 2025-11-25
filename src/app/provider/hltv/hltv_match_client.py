import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional

from bs4 import BeautifulSoup

from src.app.html.HtmlParserService import HtmlParserService
from src.app.provider.hltv.dto.HltvMatchResponse import HltvMatchResponse
from src.app.provider.hltv.dto.HltvStream import HltvStream
from src.app.provider.hltv.dto.HltvTeamBrief import HltvTeamBrief

logger = logging.getLogger(__name__)


class HltvMatchClient:
  BASE_URL = "https://www.hltv.org"

  def __init__(self, html_parser: HtmlParserService):
    self._html_parser = html_parser

  async def sync_future_matches(self, team_id: str, slug: str) -> List[
    HltvMatchResponse]:
    match_response = await self.sync_matches(team_id, slug)

    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)

    return [
      match for match in match_response
      if match.datetime >= two_hours_ago
    ]

  async def sync_matches(self, team_id: str, slug: str) -> List[
    HltvMatchResponse]:
    """
    Fetch recent match results for a specific HLTV team.
    """
    url = f"{self.BASE_URL}/team/{team_id}/{slug}"
    soup = self._html_parser.parse(url)
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

      team1 = team_names[0]
      team1Dto = self.extract_id(team1)

      team2 = team_names[1]
      team2Dto = self.extract_id(team2)

      scores = tr.select("div.score-cell span.score")
      score1 = int(scores[0].text.strip()) if len(scores) > 0 and scores[
        0].text.strip().isdigit() else None
      score2 = int(scores[1].text.strip()) if len(scores) > 1 and scores[
        1].text.strip().isdigit() else None

      match_url, match_id = self.extract_match_url(tr)

      return HltvMatchResponse(
        match_id=match_id,
        match_url=match_url,
        datetime=match_datetime,
        team1=team1Dto,
        team2=team2Dto,
        score1=score1,
        score2=score2,
      )
    except Exception as e:
      logger.error(f"Error parsing row: {e}")
      return None

  def extract_match_url(self, tr) -> tuple[Optional[str], Optional[int]]:
    links = tr.select("a[href]")
    match_url = None
    match_id = None

    for a in links:
      href = a["href"]
      if href.startswith("/matches/"):
        match_url = f"{self.BASE_URL}{href}"
        m = re.search(r"/matches/(\d+)", href)
        match_id = int(m.group(1)) if m else None
        break
    return match_url, match_id

  def extract_id(self, team_tags) -> Optional[HltvTeamBrief]:
    if not team_tags:
      return None

    name = team_tags.text.strip()
    href = team_tags.get("href", "")
    parts = href.split("/")
    team_id = int(parts[2]) if len(parts) > 2 else None
    team_slug = parts[3] if len(parts) > 3 else None
    return HltvTeamBrief(team_id, name, team_slug)

  async def _enrich_match_details(self, match: HltvMatchResponse):
    if not match.match_url:
      return

    try:
      soup = self._html_parser.parse(match.match_url)
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
