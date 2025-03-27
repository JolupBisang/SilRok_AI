from typing import List
from fastapi import APIRouter, UploadFile, File

from schemas.whisper import Segment
from services import AppState 

router = APIRouter()

def raw_to_obj(segmentation):
  result = []
  for segment in segmentation:
    result.append(
      Segment(
        id=segment.id, 
        start=segment.start,
        end=segment.end,
        text=segment.text
    ))

  return result

@router.get("/stt", response_model=List[Segment])
async def stt_byte(audio: bytes, language: str = "ko"):
  state = AppState.get_instance()
  segmentation, _ = await state.thread_manager.submit_to_executor(
    state.whisper.translate, audio, language
  )

  return raw_to_obj(segmentation)

@router.post("/stt", response_model=List[Segment])
async def stt_file(audio: UploadFile = File(...), language: str = "ko"):
  audio_bytes = await audio.read()

  state = AppState.get_instance()
  segmentation, _ = await state.thread_manager.submit_to_executor(
    state.whisper.translate, audio_bytes, language
  )

  return raw_to_obj(segmentation)
