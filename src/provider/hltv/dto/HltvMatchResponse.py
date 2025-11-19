from dataclasses import field
from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

from src.provider.hltv.dto.HltvStream import HltvStream


class HltvMatchResponse(BaseModel):
    event_name: Optional[str] = None
    event_url: Optional[str] = None
    match_id: Optional[int]
    match_url: Optional[str]
    datetime: datetime
    team1: str
    team2: Optional[str]
    score1: Optional[int]
    score2: Optional[int]
    best_of: Optional[int] = None
    streams: List[HltvStream] = field(default_factory=list)
