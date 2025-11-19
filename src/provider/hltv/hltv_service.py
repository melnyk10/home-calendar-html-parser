import logging

from src.provider.hltv.hltv_match_client import HltvMatchesClient
from src.provider.hltv.hltv_team_client import HltvTeamClient

logger = logging.getLogger(__name__)


class HltvService:
  def __init__(self):
    self._hltv_calendar_client = HltvMatchesClient()
    self._hltv_team_client = HltvTeamClient()
