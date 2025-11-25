import logging

import grpc

from src.app.config.settings import settings
from src.app.proto_generated import hltv_pb2_grpc
from src.app_grpc.hltv_service import HltvService

logger = logging.getLogger(__name__)


async def serve() -> None:
  server = grpc.aio.server()

  hltv_pb2_grpc.add_HltvServiceServicer_to_server(HltvService(), server)

  bind_addr = f"{settings.grpc_host}:{settings.grpc_port}"
  logger.info("Starting gRPC server on %s", bind_addr)
  server.add_insecure_port(bind_addr)

  await server.start()
  await server.wait_for_termination()