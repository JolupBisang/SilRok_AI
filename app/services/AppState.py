from fastapi import FastAPI
from models import Whisper
from services import ThreadManager

class AppState:
  implementation:"AppState" = None

  def __init__(self):
    if AppState.implementation is not None:
      raise Exception("Routine is a singleton class. Use Routine.get_instance() instead.")

    self.__thread_manager:ThreadManager = ThreadManager()
    self.__whisper:Whisper = Whisper()

  @property
  def whisper(self):
    return self.__whisper
  
  @property
  def thread_manager(self):
    return self.__thread_manager

  @staticmethod
  def get_instance():
    return AppState.implementation

  @staticmethod
  def startup(app:FastAPI):
    print("🚀 FastAPI 서버 시작!")

    AppState.implementation = AppState()
    
  @staticmethod
  def shutdown(app: FastAPI):
    print("🛑 FastAPI 서버 종료!")

    if AppState.implementation.thread_manager is None:
      raise Exception("First, you need to call Routine.startup()")
    AppState.implementation.thread_manager.close()

  