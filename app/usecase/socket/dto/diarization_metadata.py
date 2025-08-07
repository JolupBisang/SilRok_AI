from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

from dataclasses import dataclass
from functools import cached_property

from core.config import Config
from util.util import bytes_to_np, decompress_from_opus, mp4_bytes_to_ndarray

from services.embed import EmbedInput
from services.rt_diarization import RTDiarizationInput
from usecase.socket.dto.flag import DIARIZATION_EMBED

if TYPE_CHECKING:
    from usecase.socket.dto.metadata import Metadata


SAMPLE_RATE = Config.get_instance().config.service.sample_rate
MIN_DURATION = 8000
EMBEDDING_LENGTH = 512 * 4  # 4 bytes for float32


@dataclass
class DiarizationMetadata:
    metadata: Metadata

    @property
    def flag(self):
        return self.metadata.flag

    @property
    def group_id(self):
        return self.metadata.header["group_id"]

    @property
    def user_id(self):
        return self.metadata.header["user_id"]

    @property
    def user_ids(self):
        return self.metadata.header.get("user_ids", [])

    @property
    def counts(self):
        return self.metadata.header.get("counts", [])

    @property
    def sc_offset(self):
        return self.metadata.header.get("sc_offset", None)

    @cached_property
    def audio(self):
        if len(self.metadata.payload) == 0:
            raise ValueError("No audio data found in metadata payload")
        if self.flag == DIARIZATION_EMBED:
            audio = mp4_bytes_to_ndarray(self.metadata.payload, SAMPLE_RATE)
            if audio.shape[0] < MIN_DURATION:
                raise ValueError(
                    f"Audio length {audio.shape[0]} is less than minimum required duration {MIN_DURATION}"
                )
        else:
            audio = (np.frombuffer(self.metadata.payload, dtype=np.int16) / 32768.0).astype(np.float32)
            # nan등 이상치 처리
            # audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
        return audio

    def to_refer(self):
        length = len(self.metadata.payload)
        if length == 0:
            raise ValueError("No refer data found in metadata payload")

        start = 0
        refer_dict = {}
        for user_id, count in zip(self.user_ids, self.counts):
            refer_dict[user_id] = []
            for _ in range(count):
                end = start + EMBEDDING_LENGTH
                refer_dict[user_id].append(
                    np.frombuffer(
                        self.metadata.payload[start:end],
                        dtype=np.float32,
                    )
                )
                start = end
        return refer_dict

    def to_embed_input(self, sr = SAMPLE_RATE):
        return EmbedInput(
            user_id=self.user_id,
            audio=self.audio,
            sample_rate=sr,
        )

    def to_rt_diarization_input(self, sid: str, refer:dict):
        return RTDiarizationInput(
            uuid=sid,
            audio=self.audio,
            group_id=self.group_id,
            user_id=self.user_id,
            refer_dict=refer,
            sc_offset=self.sc_offset,
        )

    @staticmethod
    def from_metadata(metadata: Metadata):
        return DiarizationMetadata(
            metadata=metadata,
        )
