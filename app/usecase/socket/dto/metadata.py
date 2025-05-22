from dataclasses import dataclass, field
from typing import Union

import numpy as np

from core import Settings
from util.util import bytes_to_np, decompress_from_opus

from .flag import *

EMBEDDING_LENGTH = 512 * 4  # 4 bytes for float32


@dataclass(slots=True)
class Metadata:
    flag: str
    user_id: int
    group_id: int
    audio: Union[np.ndarray, None] = field(default=None)
    refer: Union[dict, None] = field(default=None)
    metadata: Union[dict, None] = field(default=None)

    @staticmethod
    def __get_dict(data: bytes, loads: callable):
        end = 4 + int.from_bytes(data[0:4], byteorder="big")
        return loads(data[4:end]), data[end:]

    @staticmethod
    def __get_audio(data: bytes):
        if len(data) == 0:
            return np.zeros((0,), dtype=np.float32)
        audio, _ = decompress_from_opus(data)
        audio = bytes_to_np(data, Settings.MODEL_SAMPLE_RATE)
        audio = audio.astype(np.float32)
        return audio

    @staticmethod
    def __get_refer(data: bytes, loads: callable):
        refer_dict, left = Metadata.__get_dict(data, loads)

        start = 0
        new_refer_dict = {}
        for k in refer_dict:
            new_refer_dict[k] = []
        for k, v in refer_dict.items():
            for _ in range(v):
                end = start + EMBEDDING_LENGTH
                new_refer_dict[k].append(
                    np.frombuffer(left[start:end], dtype=np.float32)
                )
                start = end

        return new_refer_dict

    @staticmethod
    def __get_metadata(data: bytes, loads: callable):
        return Metadata.__get_dict(data, loads)[0]

    @staticmethod
    def from_dict(data: dict):
        flag = data["type"]
        if flag not in FLAGS:
            raise ValueError(f"Invalid flag: {flag}")

        return Metadata(
            flag=flag,
            user_id=data.get("user_id", None),
            group_id=data.get("group_id", None),
        )

    @staticmethod
    def from_byte(data: bytes, loads: callable):
        dic, left = Metadata.__get_dict(data, loads)
        metadata = Metadata.from_dict(dic)

        if metadata.flag == DIARIZATION:
            metadata.audio = Metadata.__get_audio(left)
        elif metadata.flag == DIARIZATION_REFER:
            metadata.refer = Metadata.__get_refer(left, loads)
        elif metadata.flag == METADATA:
            metadata.metadata = Metadata.__get_metadata(left, loads)

        return metadata
