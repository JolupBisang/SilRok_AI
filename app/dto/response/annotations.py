from typing import Annotated
from pydantic import Field


GroupId = Annotated[
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

Agenda = Annotated[
    list[int],
    Field(
        title="agenda list index",
        description="완료된 아젠다 인덱스를 반환, 0부터 시작",
        example=[0, 1, 2],
    ),
]

Context = Annotated[
    str,
    Field(
        title="context",
        max_length=1024,
        description="LLM이 생성한 대화 요약, 최대 출력 토큰 1024",
        example="회의 요약 내용",
    ),
]

Feedback = Annotated[
    list[dict[str, str]],
    Field(
        title="feedback",
        max_length=1024,
        description="LLM이 생성한 발화자 피드백, 최대 출력 토큰 1024",
        example=[
            {
                "name": "발화자1",
                "comment": "발화자1의 피드백 내용",
            },
            {
                "name": "발화자2",
                "comment": "발화자2의 피드백 내용",
            },
        ],
    ),
]

Embedding = Annotated[
    str,
    Field(
        min_length=2700,
        max_length=2750,
        description="화자 임베딩 (배열 길이: 512, 바이트 길이: 2048, Base64 인코딩 후 크기: 2732)",
        example="Base64(bytes(embedding))",
    ),
]


