import logging

import uvicorn
from dotenv import load_dotenv

load_dotenv()  # This loads variables from .env into os.environ

from fastapi import FastAPI

from src.api import hltv_router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(hltv_router.router)

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=8070)
