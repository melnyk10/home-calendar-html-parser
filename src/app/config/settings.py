import os
from dataclasses import dataclass


@dataclass
class Settings:
  grpc_host: str = os.getenv("GRPC_HOST", "0.0.0.0")
  grpc_port: int = int(os.getenv("GRPC_PORT", "50051"))


settings = Settings()
