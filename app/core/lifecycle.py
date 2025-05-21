import numpy as np
from fastapi import FastAPI

from core import logger
from RTWhisper.models import Whisper
from RTWhisper.data import Context
from usecase.asr import ASRUC
from usecase.diarization import DiarizationUC
from usecase.socket import SocketUC


async def startup(app: FastAPI):

    DiarizationUC.get_instance()
    ASRUC.get_instance()
    socket_uc = SocketUC.get_instance()
    await socket_uc.init()

    whisper_run()

    # logging.getLogger("uvicorn").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    logger.info("🚀 FastAPI 서버 시작!")


async def shutdown(app: FastAPI):
    socket_uc = SocketUC.get_instance()
    await socket_uc.close()

    logger.info("🛑 FastAPI 서버 종료!")


@Whisper.object
def whisper_run(whisper: Whisper):
    # 커널 충돌 문제로, whisper 모델을 먼저 실행해야 한다.

    duration = 10.0
    sample_rate = 16000 * 120
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    dummy_audio = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)

    context = Context()
    context.processed_audio = dummy_audio
    whisper.process(context)
