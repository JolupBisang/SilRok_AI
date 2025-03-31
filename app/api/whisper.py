from fastapi import APIRouter, Depends
from schemas.whisper import Sentence, SttByte, SttFile, SttStepByte
from usecase.WhisperUC import WhisperUC

router = APIRouter()

@router.get("/stt", response_model=list[Sentence])
async def stt_byte(params: SttByte = Depends()):
  whisper_uc = WhisperUC.get_instance()
  sentences = await whisper_uc.recognition_bytes(params)

  return sentences

@router.post("/stt", response_model=list[Sentence])
async def stt_file(form: SttFile = Depends()):
  whisper_uc = WhisperUC.get_instance()
  sentences = await whisper_uc.recognition_files(form)

  return sentences

@router.get("/stt_step")
async def stt_step(params: SttStepByte = Depends()):
  whisper_uc = WhisperUC.get_instance()
  sentences = await whisper_uc.recognition_step_bytes(params)

  return sentences