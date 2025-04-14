import numpy as np

from ServerObject import ServerObject
from core import settings
from data.entity import AudioRefer
from services import ThreadManagerService

from data.entity import DiarizationEntity, DiarizationResult
from models import Pyannote
from util.FixedBufferClustering import FixedBufferClustering

MIN_DURATION = 8000

class DiarizationService(ServerObject):
  
  @ThreadManagerService.object
  @Pyannote.object
  def __init__(
    self,
    thread_manager_service:ThreadManagerService,
    pyannote:Pyannote,
    MAX_SIZE:int = settings.DIARIZATION_MAX_REFER,
  ):
    super().__init__()
    self.thread_manager_service = thread_manager_service
    self.pyannote = pyannote
    self.__MAX_SIZE = MAX_SIZE

  def get_embedding(self, audio:np.ndarray):
    return self.pyannote.get_embeddings(audio)
    
  def get_init_from_refer(self, AudioRefer:AudioRefer):
    return DiarizationEntity(
      clustering = FixedBufferClustering(AudioRefer.refer_dict, self.__MAX_SIZE)
    )
    
  async def diarize(self, dirization_entity:DiarizationEntity):
    return await self.thread_manager_service.submit_to_executor(
      self.__diarize,
      dirization_entity
    )

  # 일단 이렇게 했는데, 별로다
  def __adjust_ts(self, start:int, end:int, offset:int, max_:int):
    start = max(0, start - offset)
    end = end - offset

    duration = end - start
    if duration < MIN_DURATION:
      end = min(max_, end + MIN_DURATION - duration)
      duration = end - start
      if duration < MIN_DURATION:
        end = max(0, start - MIN_DURATION + duration)
        duration = end - start
        if duration < MIN_DURATION:
          return -1, -1
    return start, end
    
  def __diarize(self, dirization_entity:DiarizationEntity): 

    clustering = dirization_entity.clustering
    audio = dirization_entity.get_audio()
    offset = dirization_entity.offset
    userId = dirization_entity.userId

    last_end_time = offset
    order = 0
    completed = {}
    for k, v in dirization_entity.completed.items():
      start, end = self.__adjust_ts(
        v.tokens[0].start,
        v.tokens[-1].end,
        offset,
        len(audio)
      )
      last_end_time = v.tokens[-1].end
      if start == -1 or end == -1: continue
      if len(audio[start:end]) < end - start:
        pass
      embbeding = self.pyannote.get_embeddings(audio[start:end])
      predict_id = clustering.add(embbeding)
      if userId == predict_id:
        completed[order] = v
        order += 1
        
    candidate = []
    for v in dirization_entity.candidate:
      start, end = self.__adjust_ts(v.start, v.end, offset, len(audio))
      if start == -1 or end == -1: continue
      if len(audio[start:end]) < end - start:
        pass
      embbeding = self.pyannote.get_embeddings(audio[start:end])
      predict_id = clustering.get_closest(embbeding)
      if userId == predict_id:
        candidate.append(v)

    new_de = DiarizationEntity(
      clustering=clustering,
      rcd_audio=audio[last_end_time - offset:],
      offset=last_end_time
    )
    return DiarizationResult(new_de, completed, candidate)
    