from ServerObject import ServerObject
from models import Gemini

from .dto import LLMContext


class LLMService(ServerObject):
    @Gemini.object
    def __init__(
        self,
        gemini: Gemini,
    ):
        super().__init__()
        self.gemini = gemini

    def send_msg(self, context: LLMContext):
        if context._model is None:
            model = self.gemini.generate()
            context._model = model

        if not context.conversation:
            raise ValueError("Conversation is empty")

        # context._response = "제미나이 테스트 문자열. 전송 완료"

        response = context._model.send_message(context._get_msg())
        context._response = response.text
        context.extract_tagged_agenda()
        context.extract_tagged_context()
        context.extract_tagged_feedback()
