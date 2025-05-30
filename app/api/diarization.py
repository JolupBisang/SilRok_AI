from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from containers import Container
from dto.request import (
    DiarizationEmbedRequest,
    DiarizationReferRequest,
    DiarizationRequest,
)
from dto.response import DiarizationEmbedResponse, DiarizationResponse
from usecase.diarization import DiarizationUC

router = APIRouter()


@router.post("/embed_stream", response_model=DiarizationEmbedResponse)
@inject
async def embed_stream(
    diarization_embed_request: DiarizationEmbedRequest = Depends(
        DiarizationEmbedRequest.as_stream
    ),
    diarization_uc: DiarizationUC = Depends(Provide[Container.diarization_uc]),
):
    return await diarization_uc.embed(diarization_embed_request)


@router.post("/embed_file", response_model=DiarizationEmbedResponse)
@inject
async def embed_file(
    diarization_embed_request: DiarizationEmbedRequest = Depends(
        DiarizationEmbedRequest.as_file
    ),
    diarization_uc: DiarizationUC = Depends(Provide[Container.diarization_uc]),
):
    return await diarization_uc.embed(diarization_embed_request)


@router.post("/refer", response_model=DiarizationResponse)
@inject
async def refer(
    diarization_refer_request: DiarizationReferRequest,
    diarization_uc: DiarizationUC = Depends(Provide[Container.diarization_uc]),
):
    return await diarization_uc.refer(diarization_refer_request)


@router.post("/diarize_stream", response_model=DiarizationResponse)
@inject
async def diarize(
    diarization_request: DiarizationRequest = Depends(DiarizationRequest.as_stream),
    diarization_uc: DiarizationUC = Depends(Provide[Container.diarization_uc]),
):
    return await diarization_uc.diarize(diarization_request)


@router.post("/diarize_file", response_model=DiarizationResponse)
@inject
async def diarize_file(
    diarization_request: DiarizationRequest = Depends(DiarizationRequest.as_file),
    diarization_uc: DiarizationUC = Depends(Provide[Container.diarization_uc]),
):
    return await diarization_uc.diarize(diarization_request)
