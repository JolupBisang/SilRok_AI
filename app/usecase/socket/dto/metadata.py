from dataclasses import dataclass

from .flag import *

EMBEDDING_LENGTH = 512 * 4  # 4 bytes for float32


@dataclass(slots=True)
class Metadata:
    header: dict
    payload: bytes

    @property
    def flag(self):
        return self.header["flag"]

    @property
    def group_id(self):
        return self.header["group_id"]

    @staticmethod
    def from_bytes(data: bytes, loads: callable):
        header, payload = Metadata.byte_to_dict(data, loads)

        if header["flag"] not in FLAGS:
            raise ValueError(f"Invalid flag: {header['flag']}")

        return Metadata(
            header=header,
            payload=payload,
        )

    @staticmethod
    def byte_to_dict(data: bytes, loads: callable):
        end = 4 + int.from_bytes(data[0:4], byteorder="big")
        return loads(data[4:end]), data[end:]
