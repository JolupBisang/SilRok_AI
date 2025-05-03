from dataclasses import dataclass, field
import msgpack

from services.redis.dto import IRedisContext
from services.diarization.dto import Speak


@dataclass(slots=True)
class AlignedRedisContext(IRedisContext):
    group_id: str
    speaks: list[Speak] = field(default_factory=list)

    _KEY = "aligned"

    def __post__init__(self):
        self._KEY = f"socket:{self.group_id}:{self._KEY}"

    def get_dumps(self) -> dict[str, bytes]:
        return {
            self._KEY: msgpack.packb(
                [s.to_dict() for s in self.speaks], use_bin_type=True
            ),
        }

    def get_keys(self) -> list[tuple[str, type[bytes]]]:
        return [(self._KEY, bytes)]

    def append(self, key: str, value: list[bytes]):
        speaks = []
        for v in value:
            data = msgpack.unpackb(v, raw=False)
            for d in data:
                speaks.append(Speak.from_dict(d))
        self.speaks = speaks
