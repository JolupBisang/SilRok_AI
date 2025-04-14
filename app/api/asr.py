from fastapi import APIRouter, Depends, Request, Response, WebSocket

from data.dto.request import SttByte, SttFile, SttDuration
from data.dto.response import SentenceResponse
from usecase import DiarizedASRUC, ASRUC

router = APIRouter()

@router.get("/stt", response_model=SentenceResponse)
async def stt_byte(params: SttByte = Depends()):
  uc = ASRUC.get_instance()
  return await uc.transcribe_from_bytes(params)

@router.post("/stt", response_model=SentenceResponse)
async def stt_file(form: SttFile = Depends()):
  uc = ASRUC.get_instance()
  return await uc.transcribe_from_bytes(form)

@router.get("/stt_duration", response_model=SentenceResponse)
async def stt_step(params: SttDuration = Depends()):
  whisper_uc = ASRUC.get_instance()
  return await whisper_uc.transcribe_by_duration_from_bytes(params)

@router.post("/embedding")
async def embedding(request:Request):
  data = await request.body()
  uc = DiarizedASRUC.get_instance()
  result = await uc.get_embedding(data)
  return Response(content=result, media_type="application/octet-stream")

@router.websocket("/ws")
async def socket(websocket: WebSocket):
  uc = DiarizedASRUC.get_instance()
  await uc.add(websocket)