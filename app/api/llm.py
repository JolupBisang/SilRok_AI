from fastapi import Depends, Response
from fastapi.routing import APIRouter
from dependency_injector.wiring import inject, Provide

from containers import Container
from dto.request import LLMContextDoneRequest, LLMContextRequest, LLMMetadataRequest
from dto.response import LLMResponse, LLMContextResponse
from usecase.llm import LLMUC


router = APIRouter()


@router.get("/metadata")
@inject
async def metadata(
    llm_metadata_request: LLMMetadataRequest = Depends(),
    llm_uc: LLMUC = Depends(Provide[Container.llm_uc]),
):
    await llm_uc.metadata(llm_metadata_request)
    return Response(status_code=200)


@router.get("/context", response_model=LLMResponse)
@inject
async def context(
    llm_context_request: LLMContextRequest = Depends(),
    llm_uc: LLMUC = Depends(Provide[Container.llm_uc]),
):
    return await llm_uc.context(llm_context_request)


@router.get("/context_done", response_model=LLMContextResponse)
@inject
async def context_done(
    llm_context_request: LLMContextDoneRequest = Depends(),
    llm_uc: LLMUC = Depends(Provide[Container.llm_uc]),
):
    return await llm_uc.context_done(llm_context_request)

__all__ = ["router"]
