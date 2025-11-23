from dataclasses import dataclass


@dataclass
class HltvTeamResponse:
  rank: int
  name: str
  logo_url: str
  team_id: str
  team_id_name: str
