from fastapi import FastAPI

from core import logger
from usecase.llm import LLMUC
from usecase.diarization import DiarizationUC
from usecase.socket import SocketUC


async def startup(app: FastAPI):

    DiarizationUC.get_instance()
    LLMUC.get_instance()
    socket_uc = SocketUC.get_instance()
    await socket_uc.init()


    # logging.getLogger("uvicorn").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    logger.info("🚀 FastAPI 서버 시작!")


async def shutdown(app: FastAPI):
    socket_uc = SocketUC.get_instance()
    await socket_uc.close()

    logger.info("🛑 FastAPI 서버 종료!")

