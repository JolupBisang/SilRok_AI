import asyncio
import base64
import uuid

import numpy as np

from core import Settings, Singleton
from dto.request import (
    DiarizationEmbedRequest,
    DiarizationReferRequest,
    DiarizationRequest,
)
from dto.response import DiarizationEmbedResponse, DiarizationResponse
from services.embed import EmbedInput, EmbedService
from services.rt_diarization import (
    RTDiarizationInput,
    RTDiarizationOutput,
    RTDiarizationService,
)
from util.util import bytes_to_np, decompress_from_opus


class DiarizationUC(Singleton):

    @EmbedService.object
    @RTDiarizationService.object
    def __init__(
        self,
        embed_service: EmbedService,
        rt_diarization_service: RTDiarizationService,
        SAMPLE_RATE: int = Settings.MODEL_SAMPLE_RATE,
    ):
        super().__init__()
        self.embed_service = embed_service
        self.rt_diarization_service = rt_diarization_service
        self.__SAMPLE_RATE = SAMPLE_RATE

    async def __diarize(
        self, group_id: str, user_id: str, audio: np.ndarray, refer: dict = {}
    ):
        uid = uuid.uuid4()
        X = RTDiarizationInput(
            uuid=uid,
            group_id=group_id,
            user_id=user_id,
            audio=audio,
            refer_dict=refer,
            must_return=True,
        )
        fut = asyncio.get_running_loop().create_future()

        async def callback(Y: RTDiarizationOutput):
            fut.set_result(Y)

        await self.rt_diarization_service.add_callback(uid, callback)
        await self.rt_diarization_service.request(X)
        Y = await fut
        await self.rt_diarization_service.remove_callback(uid)
        return DiarizationResponse.from_rt_diarization_output(Y)

    async def __embed(self, audio: np.ndarray, sample_rate: int):
        # ㅋㅋ 극한의 압축
        return DiarizationEmbedResponse(
            embedding=base64.b64encode(
                (
                    await self.embed_service.embed(
                        EmbedInput(
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
        return await self.__diarize(
            group_id=diarization_request.group_id,
            user_id=diarization_request.user_id,
            audio=self.__bytes_to_np(diarization_request.audio, self.__SAMPLE_RATE),
        )

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

        return await self.__diarize(
            group_id=diarization_refer_request.group_id,
            user_id=diarization_refer_request.user_id,
            audio=np.zeros((0,), dtype=np.float32),
            refer=refer,
        )

    async def embed(self, diarization_embed_request: DiarizationEmbedRequest):
        return await self.__embed(
            self.__bytes_to_np(
                diarization_embed_request.audio, diarization_embed_request.sample_rate
            ),
            diarization_embed_request.sample_rate,
        )
