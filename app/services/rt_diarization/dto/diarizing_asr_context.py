from dataclasses import dataclass, field

from services.rt_diarization.asr import ASRContext
from services.rt_diarization.diarization import (
    DiarizationContext,
    FixedBufferClustering,
)

from .diarizing_asr_input import DiarizingASRInput


@dataclass(slots=True)
class DiarizingASRContext:
    uuid: str
    group_id: str
    user_id: str
    asr_context: ASRContext = field(default=None)
    diarization_context: DiarizationContext = field(default=None)

    def update(self, X: DiarizingASRInput):
        self.uuid = X.uuid
        if self.group_id != X.group_id:
            raise ValueError("group_id mismatch")
        if self.user_id != X.user_id:
            raise ValueError("user_id mismatch")

        self.asr_context.update(X.audio, X.prompt, X.language)
        self.diarization_context.update_audio(X.audio)

    def update_diarization(self):
        self.diarization_context.update(
            self.asr_context.completed, self.asr_context.candidate
        )

    @staticmethod
    def from_diarizing_asr_input(X: DiarizingASRInput):
        uuid = X.uuid
        user_id = X.user_id
        group_id = X.group_id
        asr_context = ASRContext()

        diarization_context = DiarizationContext(
            user_id=user_id,
            clustering=FixedBufferClustering(X.refer_dict),
        )

        return DiarizingASRContext(
            uuid = uuid,
            group_id=group_id,
            user_id=user_id,
            asr_context=asr_context,
            diarization_context=diarization_context,
        )
