from dataclasses import dataclass
from functools import cached_property

import numpy as np

from config import Config
from util.util import bytes_to_np, decompress_from_opus

from .metadata import Metadata

SAMPLE_RATE = Config.get_instance().config.service.sample_rate
EMBEDDING_LENGTH = 512 * 4  # 4 bytes for float32


@dataclass
class DiarizeMetadata:
    metadata: Metadata

    @property
    def flag(self):
        return self.metadata.flag

    @property
    def group_id(self):
        return self.metadata.group_id

    @property
    def user_id(self):
        return self.metadata.header["user_id"]

    @property
    def sc_offset(self):
        return self.metadata.header.get("sc_offset", None)

    @cached_property
    def audio(self):
        if len(self.metadata.payload) == 0:
            return None
        return DiarizeMetadata.__byte_to_audio(self.metadata.payload)

    def refer(self, loads: callable):
        if len(self.metadata.payload) == 0:
            return None

        data, left = Metadata.byte_to_dict(self.metadata.payload, loads)

        start = 0
        new_refer_dict = {}
        for k in data:
            new_refer_dict[k] = []
        for k, v in data.items():
            for _ in range(v):
                end = start + EMBEDDING_LENGTH
                new_refer_dict[k].append(
                    np.frombuffer(left[start:end], dtype=np.float32)
                )
                start = end

        return new_refer_dict

    @staticmethod
    def from_metadata(metadata: Metadata):
        return DiarizeMetadata(
            metadata=metadata,
        )

    @staticmethod
    def __byte_to_audio(data: bytes):
        audio, _ = decompress_from_opus(data)
        audio = bytes_to_np(audio, SAMPLE_RATE)
        return audio.astype(np.float32)
