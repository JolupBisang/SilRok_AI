from logging import Logger
import numpy as np
import pysbd
import kss

from core import settings
from ServerObject import ServerObject
from models import Whisper
from services.LoggerService import LoggerService

class Word:
  def __init__(self, start:float, end:float, text:str):
    self.__start = start
    self.__end = end
    self.__text = text

  def __str__(self) -> str:
    return f"{self.__start} {self.__end} {self.__text}"

  @property
  def start(self) -> float:
    return self.__start

  @property
  def end(self) -> float:
    return self.__end

  @property
  def text(self) -> str:
    return self.__text

class Sentence:
  def __init__(self, lang:str, text:str, audio:np.ndarray, tokens:list):
    self.__lang = lang
    self.__text = text
    self.__audio = audio
    self.__words = []

    for token in tokens:
      if isinstance(token, Word):
        self.__words.append(token)
        continue
      self.__words.append(Word(token.start, token.end, token.word))
  
  def __str__(self) -> str:
    return f"{self.__lang} {self.__text} {self.__words}"

  @property
  def lang(self) -> str:
    return self.__lang
  @property
  def text(self) -> str:
    return self.__text
  @property
  def audio(self) -> np.ndarray:
    return self.__audio
  @property
  def words(self) -> list[Word]:
    return self.__words

class KSSTokenizer:
  # KSSTokenizer likes Segmenter
  def segment(self, text) -> list[str] | list[list[str]]:
    # Use kss to segment the text
    return kss.split_sentences(text)

class Tokenizer:
  tokenizers:dict[pysbd.Segmenter] = {}
    
  @staticmethod
  def get_tokenizer(lang: str) -> pysbd.Segmenter:
    # whisper와 지원하는 언어 차이를 확인해야 한다.
    lang = lang.strip()
    if lang not in Tokenizer.tokenizers:
      if lang == "ko":
        Tokenizer.tokenizers[lang] = KSSTokenizer()
      else:
        try:
          Tokenizer.tokenizers[lang] = pysbd.Segmenter(language=lang)
        except Exception as e:
          print(f"Tokenizer not found for {lang}. Error: {e}. 이거 whisper하고 비교해서 제대로 되게 만들어야 함")
          return None
    return Tokenizer.tokenizers[lang]

class WhisperService(ServerObject):
  @Whisper.object
  def __init__(
    self,
    whisper:Whisper,
    max_pre_recog:int = 2,
    sample_rate:int = settings.MODEL_SAMPLE_RATE
  ):
    super().__init__()

    self.__SAMPLE_RATE = sample_rate
    self.__MAX_PRE_RECOG = max_pre_recog
    self.__whisper = whisper

  def get_prompt(self, pre_sentence:Sentence = None) -> str:
    return pre_sentence.text if pre_sentence else ""
  
  def get_audio(self, audio:np.ndarray, pre_recog:list[Sentence] = []) -> np.ndarray:
    new_audio = np.zeros(0, dtype=np.float32)
    for sentence in pre_recog:
      new_audio = np.concatenate([new_audio, sentence.audio])
    new_audio = np.concatenate([new_audio, audio])
    return new_audio

  @LoggerService.object
  def recognition_step(
    self,
    audio:np.ndarray,
    order:int,
    prompt:str = None,
    pre_sentence:Sentence = None,
    pre_recog: list[Sentence] = [],
    language:str = None,
    logger_service:Logger = None,
  ) -> tuple[dict[int, str], int, Sentence, list[Sentence]]:
    prompt = (prompt + " " if prompt else "") + self.get_prompt(pre_sentence)
    audio = self.get_audio(audio, pre_recog)

    sentences = self.recognition(audio, prompt, language)
    completed, pre_sentence_, pre_recog = (
      sentences[:-self.__MAX_PRE_RECOG], 
      sentences[-(self.__MAX_PRE_RECOG + 1)] if len(sentences) > self.__MAX_PRE_RECOG else None, 
      sentences[-self.__MAX_PRE_RECOG:]
    )
    
    completed_dict = {}
    for o, sentence in enumerate(completed, order):
      completed_dict[o] = sentence

    if pre_sentence_:
      pre_sentence = pre_sentence_

    logger_service.info("-" * 20)
    logger_service.info(f"Completed sentences: {[(key, value.text) for key, value in completed_dict.items()]}")
    logger_service.info(f"Pre recog sentences: {[p.text for p in pre_recog]}")
    
    return completed_dict, order + len(completed), pre_sentence, pre_recog

  def recognition(
    self,
    audio:np.ndarray,
    prompt:str = None,
    language:str = None,
  ):
    segments, info = self.__whisper.translate(audio, language, prompt)
    return self.segment_word(audio, list(segments), info)

  @LoggerService.object
  def segment_word(
    self, 
    audio:np.ndarray, 
    segments, 
    info, 
    logger_service:Logger
  ):
    lan = info.language
    tokenizer = Tokenizer.get_tokenizer(lan)
    
    sentences = []
    end = 0
    for idx, segment in enumerate(segments, 1):
      text = segment.text
      words = segment.words
      start = end
      end = segment.end if len(segments) > idx else len(audio) / self.__SAMPLE_RATE

      if tokenizer is None:
        logger_service.warning(f"Tokenizer not found for {lan}.")
        sentences.append(Sentence(
          lan, 
          text,
          audio[int(start * self.__SAMPLE_RATE):int(end * self.__SAMPLE_RATE)],
          words
        ))
        continue

      scents = tokenizer.segment(text)
      idx_end = 0
      ed = start
      for scent in scents:
        idx_start = idx_end
        idx_end = idx_start + len(scent.split(" "))

        st = ed
        ed = words[idx_end].start if len(words) > idx_end else end

        ad_st = int(st * self.__SAMPLE_RATE)
        ad_ed = int(ed * self.__SAMPLE_RATE)
        ad = audio[ad_st:ad_ed]
        sentences.append(Sentence(
          lan, 
          scent, 
          ad,
          words[idx_start:idx_end]
        ))
      
      end = ed
      
    return sentences