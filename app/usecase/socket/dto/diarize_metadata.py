from dataclasses import dataclass
from functools import cached_property

import numpy as np

from core import Config
from util.util import bytes_to_np, decompress_from_opus, mp4_bytes_to_ndarray

from .metadata import Metadata

SAMPLE_RATE = Config.get_instance().config.service.sample_rate
MIN_DURATION = 8000
EMBEDDING_LENGTH = 512 * 4  # 4 bytes for float32


@dataclass
class DiarizeMetadata:
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
            return None
        audio = DiarizeMetadata.__byte_to_audio(self.metadata.payload)
        if audio.shape[0] < MIN_DURATION:
            raise ValueError(
                f"Audio length {audio.shape[0]} is less than minimum required duration {MIN_DURATION}"
            )

    def refer(self):
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

    @staticmethod
    def from_metadata(metadata: Metadata):
        return DiarizeMetadata(
            metadata=metadata,
        )

    @staticmethod
    def __byte_to_audio(data: bytes):
        # opus decode
        # audio, _ = decompress_from_opus(data)
        # audio = bytes_to_np(audio, SAMPLE_RATE)
        # return audio.astype(np.float32)

        # NOTE  이건 임시로 한거다.. .좀 별로긴한데 프론트에서 통일 하는걸 빼먹었다.
        return mp4_bytes_to_ndarray(data, SAMPLE_RATE)

        # bytes decode
        # return np.frombuffer(data, dtype=np.float32)
