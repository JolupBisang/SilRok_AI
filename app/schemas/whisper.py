from fastapi import Query, File, UploadFile, Form
from pydantic import BaseModel

class Word(BaseModel):
  start:float
  end:float
  text:str
  lang:str


class Sentence(BaseModel):
  order:int
  lang:list[str]
  text:str
  words:list[Word]


class SttByte:
  def __init__(
    self, 
    audio:str = Query(
      description= "Audio bytes encoded in base64.",
      example= "audio_bytes"
    ),
    prompt:str|None = Query(
      default = None,
      description= "Prompt for the audio file. Default is None.",
      example= "prompt"
    ),
    language:str|None = Query(
      default = None,
      description= "Language of the audio file. Default is None.",
      example= "ko"
    )
  ):
    self.audio = audio
    self.prompt = prompt
    self.language = language


class SttFile:
  def __init__(
    self,
    audio:UploadFile = File(
      description= "Audio file.",
      example= "audio_bytes"
    ),
    prompt:str|None = Form(
      default = None,
      description= "Prompt for the audio file. Default is None.",
      example= "prompt"
    ),
    language:str|None = Form(
      default = None,
      description= "Language of the audio file. Default is None.",
      example= "ko"
    )
  ):
    self.audio = audio
    self.prompt = prompt
    self.language = language


class SttDuration:
  def __init__(
    self, 
    audio:str = Query(
      description= "Audio bytes encoded in base64.",
      example= "audio_bytes"
    ),
    group:str = Query(
      description= "Group name. This is used to identify the group of audio files.",
      example= "group"
    ),
    user:str = Query(
      description= "User name. This is used to identify the user of the audio files.",
      example= "user"
    ),
    language:str|None = Query(
      default = None,
      description= "Language of the audio file. Default is None.",
      example= "ko"
    )
  ):
    self.audio = audio
    self.group = group
    self.user = user
    self.language = language

class SttSentence:
  def __init__(
    self, 
    audio:str = Query(
      description= "Audio bytes encoded in base64.",
      example= "audio_bytes"
    ),
    group:str = Query(
      description= "Group name. This is used to identify the group of audio files.",
      example= "group"
    ),
    user:str = Query(
      description= "User name. This is used to identify the user of the audio files.",
      example= "user"
    ),
    prompt:str|None = Query(
      default = None,
      description= "Prompt for the audio file. Default is None.",
      example= "prompt"
    ),
    language:str|None = Query(
      default = None,
      description= "Language of the audio file. Default is None.",
      example= "ko"
    )
  ):
    self.audio = audio
    self.group = group
    self.user = user
    self.prompt = prompt
    self.language = language
    

class SentenceResponse(BaseModel):
  completed: list[Sentence]
  candidate: list[Word]

class DurationResponse(BaseModel):
  completed: list[Sentence]
  candidate: list[Word]
  