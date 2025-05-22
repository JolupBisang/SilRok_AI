from pydantic import BaseModel, Field

from RTWhisper.data import Sentence as WhisperSentence
from services.rt_diarization import Speak
from .word import Word


class Sentence(BaseModel):
    order: int
    lang: list[str]
    text: str
    words: list[Word]
    user_id: str = Field(default=None)
    audio_id: str = Field(default=None)

    @staticmethod
    def get_from_sentence(sentence: WhisperSentence):
        return Sentence(
            order=sentence.order,
            lang=sentence.lang,
            text=sentence.text,
            words=[Word.get_from_token(token) for token in sentence.tokens],
        )

    @staticmethod
    def get_from_speak(speak: Speak):
        return Sentence(
            order=speak.sentence.order,
            lang=speak.sentence.lang,
            text=speak.sentence.text,
            words=[Word.get_from_token(token) for token in speak.sentence.tokens],
            user_id=speak.user_id,
            audio_id=speak.audio_id,
        )
