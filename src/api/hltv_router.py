from typing import List

from fastapi import APIRouter

from src.app.provider.hltv.dto import HltvMatchResponse, HltvTeamResponse
from src.app.provider.hltv.hltv_match_client import HltvMatchesClient
from src.app.provider.hltv.hltv_service import HltvService
from src.app.provider.hltv.hltv_team_client import HltvTeamClient

router = APIRouter()
hltv_service = HltvService()
hltv_team_client = HltvTeamClient()
hltv_match_client = HltvMatchesClient()


@router.get("/api/v1/hltv/teams", tags=["hltv"])
async def sync_teams() -> List[HltvTeamResponse]:
  return await hltv_team_client.get_all_teams()


@router.get("/api/v1/hltv/teams/{team_id}/{slug}/matches", tags=["hltv"])
async def sync_matches(team_id: int, slug: str) -> List[HltvMatchResponse]:
  return await hltv_match_client.sync_matches(team_id, slug)
