from core import RedisByteManager, RedisStrManager
from fastapi import FastAPI

import logging
from logging import Logger
from services import ThreadManagerService, LoggerService
from usecase.WhisperUC import WhisperService

@LoggerService.object
def startup(app:FastAPI, logger_service:Logger):
  logger_service.info("🚀 FastAPI 서버 시작!")

  ThreadManagerService.get_instance()
  WhisperService.get_instance()
  RedisByteManager.get_instance()
  RedisStrManager.get_instance()

  logging.getLogger("uvicorn").setLevel(logging.WARNING)
  logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
  logging.getLogger("uvicorn.error").setLevel(logging.WARNING)


@LoggerService.object
@ThreadManagerService.object
def shutdown(
  app: FastAPI, 
  logger_service: Logger, 
  thread_manager_service: ThreadManagerService
):
  logger_service.info("🛑 FastAPI 서버 종료!")

  thread_manager_service.close()