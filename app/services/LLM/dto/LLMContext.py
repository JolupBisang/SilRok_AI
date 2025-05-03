import re

from typing import Union
from google.generativeai import ChatSession
from dataclasses import dataclass, field

from .Prompts import PROMPT, BACKGROUND, AGENDA, FEEDBACK, JUST_SEND, FINAL_PROMPT

REQUEST = 1
JUST_SEND = 2
DONE = 3


@dataclass(slots=True)
class LLMContext:
    context: str = field(default="")
    agenda: list[int] = field(default_factory=list)
    feedback: dict[str, str] = field(default_factory=dict)

    conversation: list[str] = field(default_factory=list)
    _agenda: list[str] = field(default_factory=list)
    _num_people: int = field(default=0)
    _meeting_topic: str = field(default="")
    _model: Union[ChatSession] = field(default=None)

    _response: str = field(default="")

    __mode: int = field(default=REQUEST, init=False)

    __PROMPT: str = field(default=PROMPT)
    __BACKGROUND: str = field(default=BACKGROUND)
    __AGENDA: str = field(default=AGENDA)
    __FEEDBACK: str = field(default=FEEDBACK)
    __JUST_SEND: str = field(default=JUST_SEND)
    __FINAL_PROMPT: str = field(default=FINAL_PROMPT)

    def update(
        self,
        agenda: list[str] = None,
        num_people: int = None,
        meeting_topic: str = None,
    ):
        self._agenda = agenda
        self._num_people = num_people
        self._meeting_topic = meeting_topic

    def set_mode_request(self):
        self.__mode = REQUEST

    def set_mode_just_send(self):
        self.__mode = JUST_SEND

    def set_mode_done(self):
        self.__mode = DONE

    def __get_agenda_str(self):
        agenda = ""
        for i, a in enumerate(self._agenda):
            agenda += f"{i+1}. {a}\n"

        return agenda

    def __get_msg_to_request(self):
        background = (
            self.__BACKGROUND.format(
                num_people=self._num_people, meeting_topic=self._meeting_topic
            )
            if self._num_people > 0 and len(self._meeting_topic)
            else ""
        )
        agenda = self.__AGENDA if self._agenda else ""
        agenda_list = self.__get_agenda_str() if self._agenda else ""
        feedback = self.__FEEDBACK  # NOTE 피드백 On/Off 있다면,
        conversation = "\n".join(self.conversation)

        return self.__PROMPT.format(
            background=background,
            agenda=agenda,
            feedback=feedback,
            agenda_list=agenda_list,
            conversation=conversation,
        )

    def __get_msg_to_just_send(self):
        return self.__JUST_SEND.format(conversation="\n".join(self.conversation))

    def __get_msg_to_done(self):
        return self.__FINAL_PROMPT

    def _get_msg(self):
        if self.__mode == REQUEST:
            return self.__get_msg_to_request()
        elif self.__mode == JUST_SEND:
            return self.__get_msg_to_just_send()
        elif self.__mode == DONE:
            return self.__get_msg_to_done()
        raise ValueError("Invalid mode")

    def extract_tagged_context(self):
        text = self._response
        context_match = re.search(r"<context>(.*?)</context>", text, re.DOTALL)
        context = context_match.group(1).strip() if context_match else None
        self.context = context

    def extract_tagged_agenda(self):
        text = self._response
        agenda_match = re.search(r"<agenda>(.*?)</agenda>", text, re.DOTALL)
        agenda_raw = agenda_match.group(1).strip() if agenda_match else ""
        agenda = [int(a) for a in agenda_raw.split(",")] if agenda_raw else []
        self.agenda = agenda

    def extract_tagged_feedback(self):
        text = self._response
        feedback_matches = re.findall(
            r"<correction name=\"(.*?)\">(.*?)</correction>", text, re.DOTALL
        )

        for name, comment in feedback_matches:
            self.feedback[name] = comment.strip()

    def to_dict(self):
        return {
            "context": self.context,
            "agenda": self.agenda,
            "feedback": self.feedback,
        }
