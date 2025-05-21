from dataclasses import dataclass, field
import json
from datetime import datetime
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
    chunk_id: int
    timestamp: datetime
    audio: Union[np.ndarray, None] = field(default=None)
    refer: Union[dict, None] = field(default=None)
    metadata: Union[dict, None] = field(default=None)

    @staticmethod
    def __get_json(data: bytes):
        length = int.from_bytes(data[0:4], byteorder="big")
        end = 4 + length
        json_text = data[4:end].decode("utf-8")
        dic = json.loads(json_text)
        left = data[end:]
        return dic, left

    @staticmethod
    def __get_audio(data: bytes):
        if len(data) == 0:
            return np.zeros((0,), dtype=np.float32)
        audio, _ = decompress_from_opus(data)
        audio = bytes_to_np(data, Settings.MODEL_SAMPLE_RATE)
        audio = audio.astype(np.float32)
        return audio

    @staticmethod
    def __get_refer(data: bytes):
        refer_dict, left = Metadata.__get_json(data)

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
    def __get_metadata(data: bytes):
        metadata, _ = Metadata.__get_json(data)
        return metadata

    @staticmethod
    def from_dict(data: dict):
        flag = data["type"]
        if flag not in FLAGS:
            raise ValueError(f"Invalid flag: {flag}")

        return Metadata(
            flag=flag,
            user_id=data.get("userId", None),
            group_id=data.get("groupId", None),
            chunk_id=data.get("chunkId", None),
            timestamp=data.get("timestamp", None),
        )

    @staticmethod
    def from_byte(data: bytes):
        dic, left = Metadata.__get_json(data)
        metadata = Metadata.from_dict(dic)

        if metadata.flag == DIARIZATION_ASR:
            metadata.audio = Metadata.__get_audio(left)
        elif metadata.flag == DIARIZATION_REFER:
            metadata.refer = Metadata.__get_refer(left)
        elif metadata.flag == METADATA:
            metadata.metadata = Metadata.__get_metadata(left)

        return metadata
