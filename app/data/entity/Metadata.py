from dataclasses import dataclass
import json
from datetime import datetime

@dataclass
class Metadata:
  type:str
  userId:int
  groupId:int 
  chunkId:int
  timestamp:datetime 

  @staticmethod
  def from_dict(data:dict):
    return Metadata(
      type = data.get("type", None),
      userId = data.get("userId", None),
      groupId = data.get("groupId", None),
      chunkId = data.get("chunkId", None),
      timestamp = data.get("timestamp", None)
    )
    
  @staticmethod
  def from_byte(data:bytes):
    length = int.from_bytes(data[0:4], byteorder = "big")
    end = 4 + length
    json_text = data[4:end].decode("utf-8")
    metadata = Metadata.from_dict(json.loads(json_text))
    left = data[end:]
    return metadata, left
    