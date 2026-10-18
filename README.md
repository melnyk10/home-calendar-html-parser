# home-calendar-html-parser

A gRPC service that scrapes [HLTV.org](https://www.hltv.org) for Counter-Strike team rankings and upcoming matches. Other home-calendar services call it to build match calendars.

HLTV has no public API, and Cloudflare sends a JavaScript challenge to every non-browser client. The service fetches pages through [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr), which solves the challenge in a headless browser, and parses the HTML with BeautifulSoup.

## API

The service is defined in [`proto/hltv.proto`](proto/hltv.proto) as `home_calendar.hltv.HltvService`.

| Method | Request | Returns |
| --- | --- | --- |
| `SyncTeams` | `google.protobuf.Empty` | Teams from the HLTV world ranking: rank, name, logo URL, team ID and slug |
| `SyncMatches` | `SyncMatchesRequest { team_id, slug }` | The team's matches that start no more than 2 hours ago or later, with event, opponents, score, best-of and streams |

`team_id` and `slug` come from the team's HLTV URL. For `https://www.hltv.org/team/9565/vitality` they are `9565` and `vitality`. `SyncTeams` returns both for every ranked team.

Match times are UTC, sent as ISO-8601 strings (for example `2025-11-04T09:25:00+00:00`).

If Cloudflare still blocks a page after 3 attempts, the call fails instead of returning an empty list.

## Running locally

Requires Python 3.9 or newer and a running FlareSolverr:

```bash
docker run -d --name flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:v3.5.2
```

Then start the service:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Run commands from the repository root: the code imports modules as `src.app...`.

The server listens on `0.0.0.0:50051` by default.

### Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `GRPC_HOST` | `0.0.0.0` | Address the server binds to |
| `GRPC_PORT` | `50051` | Port the server listens on |
| `FLARESOLVERR_URL` | `http://localhost:8191/v1` | FlareSolverr API endpoint |

The first request solves the Cloudflare challenge and takes about 10 seconds. Later requests reuse the FlareSolverr session cookie and take 1–3 seconds each.

## Running with Docker

Compose starts the service together with FlareSolverr:

```bash
touch .env   # docker-compose.yml expects this file; put the variables above in it if needed
docker compose up --build
```

`docker-compose.yml` currently publishes port `8070`, but the server listens on `50051`. To call the service from the host, change the mapping to `"50051:50051"`.

Without Compose, with FlareSolverr running on the host as shown above:

```bash
docker build -t home-calendar-html-parser .
docker run --rm -p 50051:50051 \
  -e FLARESOLVERR_URL=http://host.docker.internal:8191/v1 \
  home-calendar-html-parser
```

## Calling the service

The server does not enable gRPC reflection, so pass the proto file to [grpcurl](https://github.com/fullstorydev/grpcurl):

```bash
grpcurl -plaintext -import-path proto -proto hltv.proto \
  localhost:50051 home_calendar.hltv.HltvService/SyncTeams

grpcurl -plaintext -import-path proto -proto hltv.proto \
  -d '{"team_id": "9565", "slug": "vitality"}' \
  localhost:50051 home_calendar.hltv.HltvService/SyncMatches
```

`SyncMatches` opens every match page to read the best-of format and streams, so it can take a while for teams with many listed matches.

## Changing the proto

After editing `proto/hltv.proto`, regenerate the Python code:

```bash
python3 -m grpc_tools.protoc \
  -I proto \
  --python_out=src/app/proto_generated \
  --grpc_python_out=src/app/proto_generated \
  proto/hltv.proto
```

Then change the import in `src/app/proto_generated/hltv_pb2_grpc.py` from `import hltv_pb2 as hltv__pb2` to `from . import hltv_pb2 as hltv__pb2`.

The generated code checks the installed `grpcio` version on import. Keep `grpcio` and `grpcio-tools` in `requirements.txt` on the same version you generated with.

New fields also need changes in the DTOs (`src/app/provider/hltv/dto/`) and in the `*_to_proto` functions in `src/app_grpc/hltv_service.py`.

## Project layout

```
proto/                      gRPC service definition
src/main.py                 entry point
src/app_grpc/               gRPC server and the HltvService implementation
src/app/html/               page fetching and Cloudflare handling
src/app/provider/hltv/      HLTV page parsers and DTOs
src/app/proto_generated/    generated protobuf code
```

## License

[Apache License 2.0](LICENSE)
