from pydantic import BaseModel

from RTWhisper.data import Sentence as WhisperSentence
from RTWhisper.data import Token
from data.entity import ASRResult

from .Sentence import Sentence
from .Word import Word

class SentenceResponse(BaseModel):
  completed: list[Sentence]
  candidate: list[Word]

  @staticmethod
  def get_from_result(
    completed:dict[int:WhisperSentence],
    candidate:list[Token]
  ):
    return SentenceResponse(
      completed = [
        Sentence.get_from_sentence(key, value) 
        for key, value in completed.items()
      ],
      candidate = [
        Word.get_from_token(token) for token in candidate
      ]
    )
    
  @staticmethod
  def get_from_asr_result(asr_result:ASRResult):
    return SentenceResponse(
      completed = [
        Sentence.get_from_sentence(key, value) 
        for key, value in asr_result.completed.items()
      ],
      candidate = [
        Word.get_from_token(token) for token in asr_result.candidate
      ]
    )