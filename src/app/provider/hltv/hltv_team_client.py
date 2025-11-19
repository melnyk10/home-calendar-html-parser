import asyncio
import logging
import re
from datetime import date
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

from src.app.common.consts import HEADERS
from src.app.provider.hltv.dto.HltvTeamResponse import HltvTeamResponse

logger = logging.getLogger(__name__)


class HltvTeamClient:
    BASE_URL = "https://www.hltv.org"

    async def get_all_teams(self, limit: Optional[int] = None) -> List[HltvTeamResponse]:
        year = date.today().year
        url = f"{self.BASE_URL}/ranking/teams/{year}/may/19"
        async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            team_divs = soup.select("div.ranked-team.standard-box")

            # Apply limit only if provided
            if limit is not None:
                team_divs = team_divs[:limit]

            teams = []
            for div in team_divs:
                try:
                    team = self._parse_team(div)
                    if team:
                        teams.append(team)
                except Exception as e:
                    logger.warning(f"Failed to parse team div: {e}")

            return teams

    def _parse_team(self, container) -> HltvTeamResponse:
        rank = int(container.select_one(".position").text.strip().lstrip("#"))
        name = container.select_one(".teamLine .name").text.strip()

        # More flexible logo extraction
        logo_img = container.select_one("span.team-logo img")
        logo_url = logo_img["src"] if logo_img else ""
        if logo_url and not logo_url.startswith("http"):
            # todo: set some default logo
            logo_url = None

        profile_link = container.select_one("a.moreLink[href^='/team/']")
        match = re.search(r"/team/(\d+)/([^\"/]+)", profile_link["href"]) if profile_link else None
        if not match:
            raise ValueError("Team ID and name not found in profile link")
        team_id, team_id_name = int(match.group(1)), match.group(2)

        return HltvTeamResponse(
            rank=rank,
            name=name,
            logo_url=logo_url,
            team_id=team_id,
            team_id_name=team_id_name
        )

async def main():
  client = HltvTeamClient()
  teams = await client.get_all_teams()
  print(teams)

asyncio.run(main())