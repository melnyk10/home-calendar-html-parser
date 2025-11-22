from typing import List

from google.protobuf import empty_pb2

from src.app.html.HtmlParserService import HtmlParserService
from src.app.proto_generated import hltv_pb2, hltv_pb2_grpc
from src.app.provider.hltv.dto.HltvMatchResponse import \
  HltvMatchResponse
from src.app.provider.hltv.dto.HltvStream import HltvStream
from src.app.provider.hltv.dto.HltvTeamResponse import \
  HltvTeamResponse
from src.app.provider.hltv.hltv_match_client import HltvMatchesClient
from src.app.provider.hltv.hltv_team_client import HltvTeamClient


def team_to_proto(team: HltvTeamResponse) -> hltv_pb2.HltvTeam:
  return hltv_pb2.HltvTeam(
    rank=team.rank,
    name=team.name,
    logo_url=team.logo_url or "",
    team_id=team.team_id,
    team_id_name=team.team_id_name or "",
  )


def stream_to_proto(stream: HltvStream) -> hltv_pb2.HltvStream:
  return hltv_pb2.HltvStream(
    name=stream.name or "",
    url=stream.url or "",
    language=stream.language or "",
  )


def match_to_proto(match: HltvMatchResponse) -> hltv_pb2.HltvMatch:
  score1 = match.score1 if match.score1 is not None else 0
  score2 = match.score2 if match.score2 is not None else 0
  best_of = match.best_of if match.best_of is not None else 0

  dt_str = match.datetime.isoformat()

  streams_proto = [stream_to_proto(s) for s in (match.streams or [])]

  return hltv_pb2.HltvMatch(
    event_name=match.event_name or "",
    event_url=match.event_url or "",
    match_id=match.match_id or 0,
    match_url=match.match_url or "",
    datetime=dt_str,
    team1=match.team1,
    team2=match.team2 or "",
    score1=score1,
    score2=score2,
    best_of=best_of,
    streams=streams_proto,
  )


class HltvService(hltv_pb2_grpc.HltvServiceServicer):
  def __init__(self) -> None:
    self._html_parser = HtmlParserService()
    self._team_client = HltvTeamClient(self._html_parser)
    self._match_client = HltvMatchesClient(self._html_parser)


async def SyncTeams(self, request: empty_pb2.Empty, context):
  teams: List[HltvTeamResponse] = await self._team_client.get_all_teams()
  proto_teams = [team_to_proto(t) for t in teams]
  return hltv_pb2.SyncTeamsResponse(teams=proto_teams)


async def SyncMatches(self, request: hltv_pb2.SyncMatchesRequest, context):
  matches: List[
    HltvMatchResponse] = await self._match_client.sync_future_matches(
    request.team_id, request.slug
  )
  proto_matches = [match_to_proto(m) for m in matches]
  return hltv_pb2.SyncMatchesResponse(matches=proto_matches)
