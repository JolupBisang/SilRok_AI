from dataclasses import dataclass, field
from typing import Union

import msgpack
import numpy as np

from services.redis import IRedisContext
from services.asr import ASRContext

from RTWhisper.data import Param


@dataclass(slots=True)
class RedisContext(IRedisContext):
    group_id: str
    user_id: str
    param: Union[Param, None] = field(default=None)

    _key: str = field(default="", init=False)

    def __post_init__(self):
        self._key = f"asr:{self.group_id}:{self.user_id}:td"

    def get_dumps(self) -> dict[str, Union[str, bytes]]:
        return {
            f"{self._key}:param": msgpack.packb(
                self.param.model_dump(), use_bin_type=True
            ),
            f"{self._key}:audio": self.param.audio.tobytes(),
            f"{self._key}:prev_audio": self.param.prev_audio.tobytes(),
            f"{self._key}:prev_processed_audio": self.param.prev_processed_audio.tobytes(),
        }

    def get_keys(self):
        return [
            (f"{self._key}:param", bytes),
            (f"{self._key}:audio", bytes),
            (f"{self._key}:prev_audio", bytes),
            (f"{self._key}:prev_processed_audio", bytes),
        ]

    def append(self, key: str, value: Union[str, bytes]):
        if key == f"{self._key}:param":
            self.param = (
                Param(**msgpack.unpackb(value, raw=False))
                if value is not None
                else Param()
            )
        elif key == f"{self._key}:audio":
            self.param.audio = (
                np.frombuffer(value, dtype=np.float32)
                if value is not None
                else np.zeros((0,), dtype=np.float32)
            )
        elif key == f"{self._key}:prev_audio":
            self.param.prev_audio = (
                np.frombuffer(value, dtype=np.float32)
                if value is not None
                else np.zeros((0,), dtype=np.float32)
            )
        elif key == f"{self._key}:prev_processed_audio":
            self.param.prev_processed_audio = (
                np.frombuffer(value, dtype=np.float32)
                if value is not None
                else np.zeros((0,), dtype=np.float32)
            )

    def get_asr_context(self):
        return ASRContext(param=self.param)
