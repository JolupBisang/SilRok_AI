from __future__ import annotations
from typing import TYPE_CHECKING

import random

from rt_whisper.data.token import Token
from rt_whisper.data.sentence import Sentence

from core.config import Config
from util import LRUDict
from services.rt_diarization.dto.diarizing_asr_output import DiarizingASROutput
from services.rt_diarization.dto.speak import Speak

if TYPE_CHECKING:
    from services.rt_diarization.dto import DiarizingASRInput


TEST_TEXT = """
Whisper은 97개의 언어에서의 자동 음성 인식(ASR)과 96개의 언어에서 영어로의 번역을 하는 최신 SOTA이다. Whisper 모델은 MIT license로 공개되어있다. 하지만, 현재 공개된 Whisper의 추론 구현은 보통 처리 시점에서 어떠한 시간 제약도 없이 완전히 확보된 음성 데이터만을 오프라인 처리를 허용한다.

실시간 스트리밍 모드는 실시간 자막과 같은 특정 상황에서 유용하다. 이는 입력되는 음성 오디오가 녹음되는 시간에 연산 되어야함을 의미한다. 전사 및 번역은 2초 정도의 짧은 지연 시간 동안 전달되어야한다. Whisper을 사용한 Streaming 구현도 몇몇 존재하지만 그것들의 접근 방식은 다소 단순하다. 그들은 예를들어 30초씩 오디오를 분할하고 연산한다. 그 기법들의 지연시간은 크며, 단순하게 내용을 보지 않고 분할하기에 단어가 중간에서 잘리는 경우가 있어 구간 경계의 품질또안 낮다.

이 연구에서, 우리는 간단하고 효율적인 LocalAgreement 알고리즘을 사용하여 Whisper를 동시 스트리밍 모드에서 구현, 평가 및 시연한다. LocalAgreement 알고리즘은 모든 전체 시퀀스 입출력 모델을 동시 스트리밍 모드에서 작동하도록 변환할 수 있는 스트리밍 정책 중 하나이다. 이 알고리즘은 IWSLT 2022 동시 음성 번역 공유 과제에서 우승한 시스템인 CUNI-KIT에서 사용되었다. 우리의 구현은 Whisper-Streaming이라고 부른다. 하지만, Whisper과 유사한 다른 모델에도 적용가능하다. 우리의 평가 결과에 따르면, Whisper-Streaming은 유럽 의회 연설 테스트 셋 ESIC의 영어 ASR 부문에서 3.3초의 평균 지연시간을 달성했다. 이는 고성능 처리 장치 NVIDIA A40 GPU에서 구동한 결과이다. 또한 독일어와 체코어에 대해서 ASR을 테스트 했으며, 결과와 최적 파라미터에 대한 제안도 함께 제시한다.

본 연구의 기여는 Whisper-Streaming의 구현과 평가 및 시연이다. 주어진 Whisper-Streaming은 빠르고 쉽게 제품화 될 수 있다. 우리는 동시 처리 모드용 알고리즘과 같은 최신 과학적 결과가 산업 연구원과 개발자에게 접근 가능하고 실제로 활용될 수 있도록 하는 것이 목표이다. 나아가, 우리는 Whisper-Streaming의 성능에 대한 실뢰성 있는 평가와 연구 커뮤니티에 그 결과를 공유함으로써, 실생활에서 활용 가능한 실시간 전사 솔루션의 연구 및 개발을 더욱 촉진하고자 한다. 우리는 본 연구 결과가 향후 비교 연구를 위한 강력한 기준선으로 활용될 수 있을 것으로 기대한다.

우리는 Whisper-Streaming을 시연 영상과 함께 공개한다.
""".replace("\n", "").strip()

BUFFER_SIZE = Config.get_instance().config.service.socket.max_buffer_size

test_user = LRUDict(max_size=BUFFER_SIZE * 20)


class TestDiarizingASROutput(DiarizingASROutput):
    @staticmethod
    def create_random(X: DiarizingASRInput) -> "TestDiarizingASROutput":
        uuid = X.uuid
        user_id = X.user_id
        group_id = X.group_id

        key = (user_id, group_id)
        order, sr, st, ed = test_user.get(key, (0, 0, 0, 0))
        completed, candidate = [], []

        ed += random.randint(0, 50)
        if ed > len(TEST_TEXT):
            ed = random.randint(0, 50)
            st = 0
        while ed - st > 30:
            duration = random.randint(160, 16000)
            if TEST_TEXT[st:st + 30].strip() != "":
                completed.append(generate_speak(user_id, st, st + 30, sr, duration, order))
                order += 1
            st += 30
            sr += duration

        if TEST_TEXT[st:ed].strip() != "":
            candidate.append(
                generate_speak(user_id, st, ed, sr, random.randint(160, 16000), order)
            )

        test_user[key] = (order, sr, st, ed)

        return TestDiarizingASROutput(
            uuid=uuid,
            group_id=group_id,
            user_id=user_id,
            completed=completed,
            candidate=candidate,
        )


def generate_speak(user_id: str, st: int, ed: int, sr: int, duration: int, order: int):
    cs = TEST_TEXT[st:ed]
    tokens_str = cs.split()
    assert len(tokens_str) > 0, "Tokens must not be empty"
    sr_step = duration // len(tokens_str)
    tokens = []
    for i, token in enumerate(tokens_str):
        start = sr + i * sr_step
        end = start + sr_step
        tokens.append(
            Token(
                start=start,
                end=end,
                text=token,
                lang="ko",
                tokens=[],
                probability=1,
                is_word=True,
            )
        )
    return Speak(
        similarity=1,
        user_id=user_id,
        audio_id=user_id,
        sentence=Sentence(
            order=order,
            lang=["ko"],
            text=cs,
            tokens=tokens,
        ),
    )
