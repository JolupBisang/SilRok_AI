from dataclasses import dataclass, field
import json
import numpy as np

EMBEDDING_LENGTH = 512 * 4 # 4 bytes for float32

@dataclass
class AudioRefer:
  refer_dict:dict[str:list[np.ndarray]] = field(default_factory=dict)
  
  @staticmethod
  def from_dict(data:dict):
    return AudioRefer(data)

  @staticmethod
  def from_byte(data:bytes):
    length = int.from_bytes(data[0:4], byteorder = "big")
    end = 4 + length
    json_text = data[4:end].decode("utf-8")
    refer_dict = json.loads(json_text)
    left = data[end:]

    start = 0
    new_refer_dict = {}
    for k in refer_dict: new_refer_dict[k] = []
    for k, v in refer_dict.items():
      for _ in range(v):
        end = start + EMBEDDING_LENGTH
        new_refer_dict[k].append(np.frombuffer(left[start:end], dtype=np.float32))
        start = end

    return AudioRefer(new_refer_dict)
