from pydantic import BaseModel

from RTWhisper.data import Token

class Word(BaseModel):
  start:float
  end:float
  text:str
  lang:str

  @staticmethod
  def get_from_token(token:Token):
    return Word(
      start = token.start,
      end = token.end,
      text = token.text,
      lang = token.lang
    )