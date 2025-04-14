from asyncio import Queue
import asyncio
import io
from logging import Logger
from fastapi.websockets import WebSocketState
import msgpack
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from ServerObject import ServerObject
from data.dto.response import SentenceResponse
from core import settings
from data.entity import ASREntity, AudioRefer, Metadata, DiarizationEntity, DiarizationResult
from services import ASRService, RedisService, LoggerService, DiarizationService
from util import LRUDict
from util.util import bytes_to_np, decompress_from_opus

DONE = "done"
ASR = "asr"
ASR_DONE = "asr_done"
DIARIZED = "diarized"
DIARIZED_DONE = "diarized_done"
REFER = "refer"

class DiarizedASRUC(ServerObject):

  @ASRService.object
  @RedisService.object
  @DiarizationService.object
  def __init__(
    self,
    asr_service: ASRService,
    redis_service: RedisService,
    diarization_service: DiarizationService,
    SAMPLE_RATE:int = settings.MODEL_SAMPLE_RATE,
    MAX_CONNECTIONS:int = settings.SOCKET_UC_MAX_CONNECTIONS,
    MAX_BUFFER:int = settings.SOCKET_UC_MAX_BUFFER,
  ):
    super().__init__()
    self.asr_service = asr_service
    self.redis_service = redis_service
    self.diarization_service = diarization_service

    self.__remaining_connections = MAX_CONNECTIONS
    self.__SAMPLE_RATE = SAMPLE_RATE
    self.__MAX_BUFFER = MAX_BUFFER
    
  def __get_audio(self, data: bytes):
    if len(data) == 0:
      return np.zeros((0,), dtype=np.float32)
    audio, _ = decompress_from_opus(data)
    audio = bytes_to_np(data, self.__SAMPLE_RATE)
    audio = audio.astype(np.float32)
    return audio

  async def __receiving_loop(self, web_socket: WebSocket, queue:Queue):
    metadata_dict = LRUDict(self.__MAX_BUFFER)
    completed = {}
    candidate = []
    audio = np.zeros((0,), dtype=np.float32)
    while True:
      data = await web_socket.receive_bytes()
      metadata, data = Metadata.from_byte(data)
      groupId = metadata.groupId
      userId = metadata.userId
      typ = metadata.type
      
      if groupId not in metadata_dict:
        metadata_dict[groupId] = {}
      if userId not in metadata_dict[groupId]:
        metadata_dict[groupId][userId] = {
          ASR:ASREntity(), 
          DIARIZED:DiarizationEntity(),
        }

      if typ == ASR or typ == ASR_DONE or typ == DIARIZED or typ == DIARIZED_DONE:
        audio = self.__get_audio(data)
        asr_entity:ASREntity = metadata_dict[groupId][userId][ASR]
        asr_entity.audio = audio
        asr_result = await self.asr_service.transcribe_by_duration(asr_entity)
        metadata_dict[groupId][userId][ASR] = asr_result.extract_asr_entity()

        completed = asr_result.completed
        candidate = asr_result.candidate
      if typ == DIARIZED or typ == DIARIZED_DONE:
        diarized_entity:DiarizationEntity = metadata_dict[groupId][userId][DIARIZED]
        diarized_entity.audio = audio
        diarized_entity.userId = userId
        diarized_entity.completed = completed
        diarized_entity.candidate = candidate
        diarized_result:DiarizationResult = await self.diarization_service.diarize(diarized_entity)
        metadata_dict[groupId][userId][DIARIZED] = diarized_result.diarization_entity

        completed = diarized_result.completed
        candidate = diarized_result.candidate
      elif typ == REFER:
        refer_dict = AudioRefer.from_byte(data)
        metadata_dict[groupId][userId][DIARIZED] = self.diarization_service.get_init_from_refer(refer_dict)

      if completed or candidate:
        msg = SentenceResponse.get_from_result(completed, candidate).model_dump()
        completed = {}
        candidate = []
        await queue.put(msg)

      if typ == ASR_DONE or typ == DIARIZED_DONE:
        await queue.put(DONE)
        return
    
  async def __sending_loop(self, web_socket: WebSocket, queue:Queue):
    while True:
      msg = await queue.get()
      if msg == DONE:
        return
      await web_socket.send_bytes(msgpack.packb(msg, use_bin_type=True))

  @LoggerService.object
  async def add(
    self,
    web_socket: WebSocket,
    logger_service:Logger
  ):
    try:
      if self.__remaining_connections <= 0:
        await web_socket.close()
        logger_service.warning("WebSocket connection limit reached")
        return
      await web_socket.accept()
      self.__remaining_connections -= 1
      logger_service.info(f"WebSocket connected, remain {self.__remaining_connections}")
      
      queue = Queue()

      await asyncio.gather(
        self.__receiving_loop(web_socket, queue),
        self.__sending_loop(web_socket, queue)
      )

      logger_service.info(f"ASR Done")
    except WebSocketDisconnect: pass
    except Exception as e:
      logger_service.error(f"WebSocket error: {e}")
      raise e
    finally:
      if web_socket.client_state == WebSocketState.CONNECTED:
        logger_service.info(f"WebSocket disconnected, remain {self.__remaining_connections}")
        await web_socket.close()
      self.__remaining_connections += 1

  async def get_embedding(self, data:bytes):
    audio = bytes_to_np(data, self.__SAMPLE_RATE)
    embedding:np.ndarray = self.diarization_service.get_embedding(audio)
    return embedding.tobytes()