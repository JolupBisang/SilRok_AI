from google.generativeai import ChatSession
from dataclasses import dataclass, field

from services.llm.dto.llm_input import LLMInput
from services.llm.dto.prompts import PROMPT, BACKGROUND, AGENDA, FEEDBACK, JUST_SEND, FINAL_PROMPT
from services.llm.dto.flag import DONE, REQUEST, UPDATE


@dataclass(slots=True)
class LLMContext:
    group_id: str = field()
    model: ChatSession = field(repr=False)

    mode: str = field(default=REQUEST)
    agenda: str = field(default="")
    num_people: int = field(default=0)
    meeting_topic: str = field(default="")

    conversation: str = field(default_factory=str)

    __PROMPT: str = field(default=PROMPT, repr=False, init=False)
    __BACKGROUND: str = field(default=BACKGROUND, repr=False, init=False)
    __AGENDA: str = field(default=AGENDA, repr=False, init=False)
    __FEEDBACK: str = field(default=FEEDBACK, repr=False, init=False)
    __JUST_SEND: str = field(default=JUST_SEND, repr=False, init=False)
    __FINAL_PROMPT: str = field(default=FINAL_PROMPT, repr=False, init=False)

    def update(self, X: LLMInput):
        if X.group_id != self.group_id:
            raise ValueError("Context group_id does not match")

        self.mode = X.mode
        if X.conversation is not None:
            self.conversation += "\n" + X.conversation
        if X.agenda is not None and len(X.agenda) > 0:
            agenda = ""
            for i, a in enumerate(X.agenda):
                agenda += f"{i+1}. {a}\n"
            self.agenda = X.agenda
        if X.num_people is not None:
            self.num_people = X.num_people
        if X.meeting_topic is not None:
            self.meeting_topic = X.meeting_topic

    def __request(self):
        # NOTE llm  출력 이상하다면 여기 볼 것
        background = (
            self.__BACKGROUND.format(
                num_people=self.num_people, meeting_topic=self.meeting_topic
            )
            if self.num_people > 0 and len(self.meeting_topic)
            else ""
        )
        agenda = self.__AGENDA if self.agenda else ""
        agenda_list = self.agenda
        feedback = self.__FEEDBACK  # NOTE 피드백 On/Off 있다면,
        conversation = self.conversation

        return self.__PROMPT.format(
            background=background,
            agenda=agenda,
            feedback=feedback,
            agenda_list=agenda_list,
            conversation=conversation,
        )

    def __update(self):
        return self.__JUST_SEND.format(conversation=self.conversation)

    def __done(self):
        return self.__FINAL_PROMPT

    def get_prompt(self):
        if self.mode == REQUEST:
            return self.__request()
        elif self.mode == UPDATE:
            return self.__update()
        elif self.mode == DONE:
            return self.__done()
        else:
            raise ValueError(
                f"Invalid mode: {self.mode}. Must be one of {DONE}, {REQUEST}, {UPDATE}."
            )

__all__ = ["LLMContext"]
