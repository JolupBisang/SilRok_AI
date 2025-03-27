from pydantic import BaseModel

class Segment(BaseModel):
  id: int
  start: float
  end: float
  text: str