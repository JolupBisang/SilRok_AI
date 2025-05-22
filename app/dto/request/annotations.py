from typing import Annotated

from fastapi import File, Query
from pydantic import Field

from core import Settings

# Query

GroupId = Annotated[
    str,
    Query(
        pattern=r"^[A-Za-z0-9]{1,255}$",
        min_length=1,
        max_length=255,
        title="group_id",
        description="미팅 고유 ID (숫자·영문, 1-255자)",
        examples={
            "default": {"summary": "기본 예시", "value": "Meeting123"},
            "numeric": {"summary": "숫자 ID", "value": "20240522"},
        },
    ),
]

UserId = Annotated[
    str,
    Query(
        pattern=r"^[A-Za-z0-9]{1,255}$",
        min_length=1,
        max_length=255,
        title="user_id",
        description="화자 고유 ID (숫자·영문, 1-255자)",
        examples={
            "default": {"summary": "기본 유저 ID", "value": "User123"},
            "anon": {"summary": "익명 사용자", "value": "Speaker007"},
        },
    ),
]

SampleRate = Annotated[
    int,
    Query(
        title="sample_rate",
        description=f"샘플링 주파수 (Hz), 모델은 {Settings.MODEL_SAMPLE_RATE}kHz를 사용하기 때문에, diarization에 사용할 시, {Settings.MODEL_SAMPLE_RATE}Hz로 변환 필요",
        examples={
            "default": {
                "summary": "기본 샘플레이트",
                "value": Settings.MODEL_SAMPLE_RATE,
            },
            "high": {"summary": "높은 샘플레이트", "value": 48000},
        },
    ),
]

Agenda = Annotated[
    str,
    Query(
        title="agenda",
        description="아젠다 (1-1024자)",
        min_length=1,
        max_length=1024,
        examples={
            "basic": {"summary": "일반 주제", "value": "웹 소켓 통신 방법에 대해 논의"},
            "detailed": {
                "summary": "구체적 논의",
                "value": "AI 기반 실시간 회의 요약 기능 개선",
            },
        },
    ),
]

AgendaList = Annotated[
    list[str] | None,  # list[Agenda] | None
    Query(
        default=None,
        title="agenda_list",
        description="아젠다 리스트, 최대 255, 번호는 자동으로 붙여주므로, 번호는 붙이지 말 것",
        min_length=1,
        max_length=255,
        examples={
            "basic": {
                "summary": "간단한 예시",
                "value": ["웹 소켓 통신 방법에 대해 논의", "AI 모델 개선 방향 논의"],
            },
        },
    ),
]

NumPeople = Annotated[
    int | None,
    Query(
        default=None,
        title="num_people",
        description="회의 참석자 수 (1-100)",
        ge=1,
        le=100,
        examples={
            "small": {"summary": "소규모", "value": 4},
            "large": {"summary": "대규모", "value": 30},
        },
    ),
]

MeetingTopic = Annotated[
    str | None,
    Field(
        default=None,
        title="meeting_topic",
        description="회의 주제 (1-4096자)",
        min_length=1,
        max_length=4096,
        examples={
            "short": {"summary": "간단 주제", "value": "웹 소켓 통신 논의"},
            "long": {
                "summary": "상세 주제",
                "value": "AI 음성 인식 기반 회의 분석 시스템 개발",
            },
        },
    ),
]


# File
AudioFile = Annotated[
    bytes,
    File(
        title="audio",
        description="wav 음성 파일을 opus로 압축한 후 base64로 인코딩한 값",
        examples={
            "base64": {
                "summary": "Base64 OPUS 데이터 예시",
                "value": "base64(opus(wav))",
            }
        },
    ),
]

# Field

GroupIdField = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9]{1,255}$",
        min_length=1,
        max_length=255,
        title="group_id",
        description="미팅 고유 ID (숫자·영문, 1-255자)",
        example="Meeting123",
    ),
]

UserIdField = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9]{1,255}$",
        min_length=1,
        max_length=255,
        title="user_id",
        description="화자 고유 ID (숫자·영문, 1-255자)",
        example="User123",
    ),
]

EmbeddingField = Annotated[
    str,
    Field(
        min_length=2700,
        max_length=2750,
        description="화자 임베딩 (배열 길이: 512, 바이트 길이: 2048, Base64 인코딩 후 크기: 2732)",
        example="Base64(bytes(embedding))",
    ),
]

ReferField = Annotated[
    dict[bytes, list[str]],  # dict[UserIdField, list[EmbeddingField]]
    Field(
        title="refer",
        description="user_id → 임베딩 매핑, 임베딩은 get 요청으로 diarization/embedding에서 생성",
        example={
            "user_id": "Base64(Aq4JqL…f2Rk)",
            "user_id2": "Base64(Aq4JqL…f2Rk)",
        },
    ),
]
