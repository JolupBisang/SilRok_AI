from pydantic import BaseModel
from dto.request.annotations import AgendaList, GroupIdField, MeetingTopic, NumPeople


class LLMMetadataRequest(BaseModel):
    group_id: GroupIdField
    agenda: AgendaList
    num_people: NumPeople
    meeting_topic: MeetingTopic
