from fastapi import Depends, Response
from fastapi.routing import APIRouter

from dto.request import LLMContextDoneRequest, LLMContextRequest, LLMMetadataRequest
from dto.response import LLMResponse
from usecase.llm import LLMUC


router = APIRouter()

@router.get("/metadata")
async def metadata(llm_metadata_request:LLMMetadataRequest = Depends()):
    await LLMUC.get_instance().metadata(llm_metadata_request)
    return Response(status_code=200)

@router.get("/context", response_model = LLMResponse)
async def context(llm_context_request:LLMContextRequest = Depends()):
    return await LLMUC.get_instance().context(llm_context_request)

@router.get("/context_done", response_model = LLMResponse)
async def context_done(llm_context_request:LLMContextDoneRequest= Depends()):
    return await LLMUC.get_instance().context_done(llm_context_request)
