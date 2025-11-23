from dataclasses import field
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from src.app.provider.hltv.dto.HltvStream import HltvStream
from src.app.provider.hltv.dto.HltvTeamBrief import HltvTeamBrief


class HltvMatchResponse(BaseModel):
  event_name: Optional[str] = None
  event_url: Optional[str] = None
  match_id: Optional[int]
  match_url: Optional[str]
  datetime: datetime
  team1: HltvTeamBrief
  team2: Optional[HltvTeamBrief]
  score1: Optional[int]
  score2: Optional[int]
  best_of: Optional[int] = None
  streams: List[HltvStream] = field(default_factory=list)
