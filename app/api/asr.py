from fastapi import APIRouter, Depends, Request, Response, WebSocket

from dto.request import SttByte, SttFile, SttDuration
from dto.response import SentenceResponse
from usecase.asr import ASRUC
from usecase.socket import SocketUC
from usecase.diarization import DiarizationUC

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


# TODO DTO 만들기
@router.post("/embedding")
async def embedding(request: Request):
    data = await request.body()
    dc = DiarizationUC.get_instance()
    result = await dc.get_embedding(data)
    return Response(content=result, media_type="application/octet-stream")


@router.websocket("/ws")
async def socket(websocket: WebSocket):
    uc = SocketUC.get_instance()
    await uc.add(websocket)
