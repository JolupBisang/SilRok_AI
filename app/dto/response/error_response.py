from dataclasses import field
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    flag: str = field(default="error")

