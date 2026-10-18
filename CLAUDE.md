# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python gRPC service that scrapes HLTV.org (CS team rankings and team match pages) and returns the data to other home-calendar services. There is no REST API (it was removed in favor of gRPC), no test suite, and no linter config.

## Commands

Run everything from the repo root. Imports are absolute from the root (`from src.app...`), so the root must be on `PYTHONPATH`.

```bash
pip install -r requirements.txt
docker run -d -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:v3.5.2   # needed for any HLTV fetch
python -m src.main                # starts the gRPC server on GRPC_HOST:GRPC_PORT (default 0.0.0.0:50051)
docker compose up --build         # service + FlareSolverr; reads .env, mounts the repo into /app
```

Regenerate gRPC code after editing `proto/hltv.proto`:

```bash
python3 -m grpc_tools.protoc \
  -I proto \
  --python_out=src/app/proto_generated \
  --grpc_python_out=src/app/proto_generated \
  proto/hltv.proto
```

protoc writes `import hltv_pb2 as hltv__pb2` in `hltv_pb2_grpc.py`. The committed file uses `from . import hltv_pb2 as hltv__pb2`; reapply that edit after regenerating or the import fails. Generated code is pinned to grpcio 1.66.0 and checks the runtime version on import, so keep `grpcio` and `grpcio-tools` in `requirements.txt` in step.

Note: `docker-compose.yml` publishes port 8070, but the server listens on 50051 (the port the Dockerfile exposes).

## Architecture

Request flow: `src/main.py` → `src/app_grpc/server.py` (`grpc.aio` server) → `src/app_grpc/hltv_service.py` (`HltvService` servicer) → HLTV clients in `src/app/provider/hltv/` → `HtmlParserService`.

- **`HtmlParserService`** (`src/app/html/`) is the single place that does HTTP. HLTV serves a Cloudflare JS challenge (`cf-mitigated: challenge`) to every non-browser client, so cloudscraper and curl_cffi don't work. The service sends requests to FlareSolverr (`FLARESOLVERR_URL`), which solves the challenge in a headless browser, and returns a `BeautifulSoup` (lxml) tree. It uses one named FlareSolverr session, so the `cf_clearance` cookie is reused after the first request. When FlareSolverr reports an error, it destroys the session, retries and finally raises `BlockedError`. That is deliberate: a challenge page would otherwise parse as an empty result. One instance is shared by both clients.
- **`HltvTeamClient.get_all_teams`** scrapes the ranking page `/ranking/teams/{current year}/may/19` (the date is hard-coded).
- **`HltvMatchClient.sync_future_matches`** scrapes `/team/{id}/{slug}`, walks `table.match-table` rows (event header rows set the current event, team rows become matches), then fetches every match page to fill `best_of` and `streams`. It keeps matches whose start is no more than 2 hours in the past. One `SyncMatches` call makes 1 + N HTTP requests.
- The client methods are `async`, but the scraping inside them is synchronous (blocking `httpx` calls to FlareSolverr + `time.sleep`), so a request blocks the event loop while it runs.
- Parsing is defensive: row-level failures are logged and skipped rather than failing the whole request.

### DTOs and proto mapping

DTOs live in `src/app/provider/hltv/dto/`. Most are dataclasses; `HltvMatchResponse` is a pydantic model. The `*_to_proto` functions in `hltv_service.py` convert DTOs to protobuf messages and replace `None` with proto defaults (`""`, `0`). When you add a field, update the `.proto`, regenerate, update the DTO, and update the mapper.

Match datetimes are timezone-aware UTC (built from the page's `data-unix` attribute) and are sent as ISO-8601 strings in `HltvMatch.datetime`.

## Code style

Two-space indentation throughout `src/` (except generated code). DTO modules are named in PascalCase after their class (`HltvMatchResponse.py`); client modules are snake_case.
