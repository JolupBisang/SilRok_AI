from pydantic import BaseModel

from dto.response.annotations import GroupId, Context, Agenda, Feedback
from services.llm import LLMOutput

class LLMResponse(BaseModel):
    group_id: GroupId
    context : Context
    agenda: Agenda
    feedback: Feedback

    @staticmethod
    def from_llm_output(Y: LLMOutput):
        return LLMResponse(
            group_id=Y.group_id,
            context=Y.context,
            agenda=Y.agenda,
            feedback=Y.feedback,
        )
