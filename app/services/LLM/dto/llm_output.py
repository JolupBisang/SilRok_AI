import re

from dataclasses import dataclass, field

from .llm_context import LLMContext


@dataclass(slots=True)
class LLMOutput:
    uuid: str
    group_id: str
    context: str = field(default="")
    agenda: list[str] = field(default_factory=list)
    feedback: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def extract_tagged_context(response: str):
        context_match = re.search(r"<context>(.*?)</context>", response, re.DOTALL)
        return context_match.group(1).strip() if context_match else None

    @staticmethod
    def extract_tagged_agenda(response: str):
        agenda_match = re.search(r"<agenda>(.*?)</agenda>", response, re.DOTALL)
        agenda_raw = agenda_match.group(1).strip() if agenda_match else ""
        return [int(a) for a in agenda_raw.split(",")] if agenda_raw else []

    @staticmethod
    def extract_tagged_feedback(response: str):
        feedback_matches = re.findall(
            r"<correction name=\"(.*?)\">(.*?)</correction>", response, re.DOTALL
        )

        feedback = {}
        for name, comment in feedback_matches:
            feedback[name] = comment.strip()

        return feedback

    @staticmethod
    def from_context_and_response(llm_context: LLMContext, response: str):
        uuid = llm_context.uuid
        group_id = llm_context.group_id
        context = LLMOutput.extract_tagged_context(response)
        agenda = LLMOutput.extract_tagged_agenda(response)
        feedback = LLMOutput.extract_tagged_feedback(response)
        return LLMOutput(
            uuid=uuid,
            group_id=group_id,
            context=context,
            agenda=agenda,
            feedback=feedback,
        )
