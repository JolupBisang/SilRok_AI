from fastapi import APIRouter, Depends

from dto.request import (
    DiarizationEmbedRequest,
    DiarizationReferRequest,
    DiarizationRequest,
)
from dto.response import DiarizationEmbedResponse, DiarizationResponse
from usecase.diarization import DiarizationUC

router = APIRouter()


@router.post("/embed_stream", response_model=DiarizationEmbedResponse)
async def embed_stream(
    diarization_embed_request: DiarizationEmbedRequest = Depends(
        DiarizationEmbedRequest.as_stream
    ),
):
    return await DiarizationUC.get_instance().embed(diarization_embed_request)


@router.post("/embed_file", response_model=DiarizationEmbedResponse)
async def embed_file(
    diarization_embed_request: DiarizationEmbedRequest = Depends(
        DiarizationEmbedRequest.as_file
    ),
):
    return await DiarizationUC.get_instance().embed(diarization_embed_request)


@router.post("/refer", response_model=DiarizationResponse)
async def refer(diarization_refer_request: DiarizationReferRequest):
    return await DiarizationUC.get_instance().refer(diarization_refer_request)


@router.post("/diarize_stream", response_model=DiarizationResponse)
async def diarize(
    diarization_request: DiarizationRequest = Depends(DiarizationRequest.as_stream),
):
    return await DiarizationUC.get_instance().diarize(diarization_request)


@router.post("/diarize_file", response_model=DiarizationResponse)
async def diarize_file(
    diarization_request: DiarizationRequest = Depends(DiarizationRequest.as_file),
):
    return await DiarizationUC.get_instance().diarize(diarization_request)
