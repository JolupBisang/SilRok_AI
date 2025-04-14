from pydantic import BaseModel

from RTWhisper.data import Sentence as WhisperSentence
from .Word import Word

class Sentence(BaseModel):
  order:int
  lang:list[str]
  text:str
  words:list[Word]

  @staticmethod
  def get_from_sentence(order:int, sentence:WhisperSentence):
    return Sentence(
      order = order,
      lang = sentence.lang,
      text = sentence.text,
      words = [
        Word.get_from_token(token) for token in sentence.tokens
      ]
    )