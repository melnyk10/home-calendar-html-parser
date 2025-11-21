from typing import List

from fastapi import APIRouter

from src.app.html.HtmlParserService import HtmlParserService
from src.app.provider.hltv.dto.HltvMatchResponse import HltvMatchResponse
from src.app.provider.hltv.dto.HltvTeamResponse import HltvTeamResponse
from src.app.provider.hltv.hltv_match_client import HltvMatchesClient
from src.app.provider.hltv.hltv_team_client import HltvTeamClient

router = APIRouter()
html_parser = HtmlParserService()
hltv_team_client = HltvTeamClient(html_parser)
hltv_match_client = HltvMatchesClient(html_parser)


@router.get("/api/v1/hltv/teams", tags=["hltv"])
async def sync_teams() -> List[HltvTeamResponse]:
  return await hltv_team_client.get_all_teams()


@router.get("/api/v1/hltv/teams/{team_id}/{slug}/matches", tags=["hltv"])
async def sync_matches(team_id: int, slug: str) -> List[HltvMatchResponse]:
  return await hltv_match_client.sync_matches(team_id, slug)
