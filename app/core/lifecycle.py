import numpy as np
from logging import Logger
from fastapi import FastAPI

from RTWhisper.models import Whisper
from RTWhisper.data import Context
from services import ThreadManagerService, LoggerService
from usecase import DiarizedASRUC, ASRUC

@LoggerService.object
def startup(app:FastAPI, logger_service:Logger):

  DiarizedASRUC.get_instance()
  ASRUC.get_instance()
  whisper_run()

  # logging.getLogger("uvicorn").setLevel(logging.WARNING)
  # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
  # logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

  logger_service.info("🚀 FastAPI 서버 시작!")


@LoggerService.object
@ThreadManagerService.object
def shutdown(
  app: FastAPI, 
  logger_service: Logger, 
  thread_manager_service: ThreadManagerService
):
  thread_manager_service.close()

  logger_service.info("🛑 FastAPI 서버 종료!")

  
@Whisper.object
def whisper_run(whisper: Whisper):
  # 커널 충돌 문제로, whisper 모델을 먼저 실행해야 한다.

  duration = 10.0
  sample_rate = 16000
  t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
  dummy_audio = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32) 

  context = Context()
  context.processed_audio = dummy_audio
  whisper.process(context)