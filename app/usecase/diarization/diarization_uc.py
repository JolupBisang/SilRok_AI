import asyncio
import base64
import uuid

import numpy as np

from dto.request import (
    DiarizationEmbedRequest,
    DiarizationReferRequest,
    DiarizationRequest,
)
from dto.response import DiarizationEmbedResponse, DiarizationResponse
from services.embed import EmbedInput, EmbedService
from services.llm import LLMInput, LLMService
from services.llm.dto.flag import UPDATE
from services.rt_diarization import (
    RTDiarizationInput,
    RTDiarizationOutput,
    RTDiarizationService,
    Speak,
)
from util.util import bytes_to_np, decompress_from_opus


class DiarizationUC:

    def __init__(
        self,
        embed_service: EmbedService,
        rt_diarization_service: RTDiarizationService,
        llm_service: LLMService,
        SAMPLE_RATE: int,
    ):
        if not isinstance(embed_service, EmbedService):
            raise TypeError("embed_service must be an instance of EmbedService")
        if not isinstance(rt_diarization_service, RTDiarizationService):
            raise TypeError(
                "rt_diarization_service must be an instance of RTDiarizationService"
            )
        if not isinstance(llm_service, LLMService):
            raise TypeError("llm_service must be an instance of LLMService")
        if not isinstance(SAMPLE_RATE, int) or SAMPLE_RATE < 8000:
            raise ValueError(
                "SAMPLE_RATE must be a positive integer greater than or equal to 8000"
            )

        super().__init__()
        self.embed_service = embed_service
        self.rt_diarization_service = rt_diarization_service
        self.llm_service = llm_service
        self.__SAMPLE_RATE = SAMPLE_RATE

    async def __llm_request(self, group_id: str, conversation: list[Speak]):
        await self.llm_service.request(
            LLMInput(
                group_id=group_id,
                conversation="\n".join(
                    f"{s.user_id}: {s.sentence.text}" for s in conversation
                ),
                mode=UPDATE,
            )
        )

    async def __diarize(
        self,
        group_id: str,
        user_id: str,
        audio: np.ndarray,
        refer: dict = {},
        sc_offset: int | None = None,
    ) -> RTDiarizationOutput:
        uid = uuid.uuid4()
        X = RTDiarizationInput(
            uuid=uid,
            group_id=group_id,
            user_id=user_id,
            audio=audio,
            refer_dict=refer,
            sc_offset=sc_offset,
            must_return=True,
        )
        fut = asyncio.get_running_loop().create_future()

        async def callback(Y: RTDiarizationOutput):
            fut.set_result(Y)

        await self.rt_diarization_service.add_callback(uid, callback)
        await self.rt_diarization_service.request(X)
        Y = await fut
        await self.rt_diarization_service.remove_callback(uid)
        return Y

    async def __embed(self, audio: np.ndarray, sample_rate: int):
        # ㅋㅋ 극한의 압축
        return DiarizationEmbedResponse(
            embedding=base64.b64encode(
                (
                    await self.embed_service.request(
                        EmbedInput(
                            user_id="",
                            audio=audio,
                            sample_rate=sample_rate,
                        )
                    )
                ).embedding.tobytes()
            ).decode("utf-8"),
        )

    def __bytes_to_np(self, opus_bytes: bytes, sample_rate: int):
        wav_bytes, _ = decompress_from_opus(opus_bytes)
        return bytes_to_np(wav_bytes, sample_rate)

    async def diarize(self, diarization_request: DiarizationRequest):
        Y = await self.__diarize(
            group_id=diarization_request.group_id,
            user_id=diarization_request.user_id,
            audio=self.__bytes_to_np(diarization_request.audio, self.__SAMPLE_RATE),
            sc_offset=diarization_request.sc_offset,
        )

        if Y.completed:
            await self.__llm_request(
                group_id=diarization_request.group_id,
                conversation=Y.completed,
            )

        return DiarizationResponse.from_rt_diarization_output(Y)

    async def refer(self, diarization_refer_request: DiarizationReferRequest):
        refer = {}
        for key, value in diarization_refer_request.refer.items():
            refer[key] = [
                np.frombuffer(
                    base64.b64decode(v),
                    dtype=np.float32,
                )
                for v in value
            ]

        return DiarizationResponse.from_rt_diarization_output(
            await self.__diarize(
                group_id=diarization_refer_request.group_id,
                user_id=diarization_refer_request.user_id,
                audio=np.zeros((0,), dtype=np.float32),
                refer=refer,
            )
        )

    async def embed(self, diarization_embed_request: DiarizationEmbedRequest):
        return await self.__embed(
            self.__bytes_to_np(
                diarization_embed_request.audio, diarization_embed_request.sample_rate
            ),
            diarization_embed_request.sample_rate,
        )
