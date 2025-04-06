from fastapi import APIRouter, Depends
from schemas.whisper import DurationResponse, Sentence, SttByte, SttFile, SttDuration
from usecase.WhisperUC import WhisperUC

router = APIRouter()

@router.get("/stt", response_model=list[Sentence])
async def stt_byte(params: SttByte = Depends()):
  whisper_uc = WhisperUC.get_instance()
  sentences = await whisper_uc.transcribe_from_byte(params)

  return sentences

@router.post("/stt", response_model=list[Sentence])
async def stt_file(form: SttFile = Depends()):
  whisper_uc = WhisperUC.get_instance()
  sentences = await whisper_uc.transcribe_from_file(form)

  return sentences

@router.get("/stt_duration", response_model=DurationResponse)
async def stt_step(params: SttDuration = Depends()):
  whisper_uc = WhisperUC.get_instance()
  sentences = await whisper_uc.transcribe_by_duration_from_byte(params)

  return sentences