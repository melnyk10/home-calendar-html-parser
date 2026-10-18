import os
from dataclasses import dataclass


@dataclass
class Settings:
  grpc_host: str = os.getenv("GRPC_HOST", "0.0.0.0")
  grpc_port: int = int(os.getenv("GRPC_PORT", "50051"))
  flaresolverr_url: str = os.getenv("FLARESOLVERR_URL", "http://localhost:8191/v1")


settings = Settings()
