import asyncio
import logging
import sys

from src.app_grpc.server import serve

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
  stream=sys.stdout,
)


def main() -> None:
  asyncio.run(serve())


if __name__ == "__main__":
  main()
