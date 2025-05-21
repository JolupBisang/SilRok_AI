from fastapi import Query


class SttSentence:
    def __init__(
        self,
        audio: str = Query(
            description="Audio bytes encoded in base64.", example="audio_bytes"
        ),
        group: str = Query(
            description="Group name. This is used to identify the group of audio files.",
            example="group",
        ),
        user: str = Query(
            description="User name. This is used to identify the user of the audio files.",
            example="user",
        ),
        prompt: str | None = Query(
            default=None,
            description="Prompt for the audio file. Default is None.",
            example="prompt",
        ),
        language: str | None = Query(
            default=None,
            description="Language of the audio file. Default is None.",
            example="ko",
        ),
    ):
        self.audio = audio
        self.group = group
        self.user = user
        self.prompt = prompt
        self.language = language
