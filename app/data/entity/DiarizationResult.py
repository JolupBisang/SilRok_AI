from dataclasses import dataclass, field

from RTWhisper.data import Sentence
from .DiarizationEntity import DiarizationEntity


@dataclass
class DiarizationResult:
  diarization_entity:DiarizationEntity = field(default_factory=DiarizationEntity)
  completed:dict[int:Sentence] = field(default_factory=dict)
  candidate:list[Sentence] = field(default_factory=list)