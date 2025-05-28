import google.generativeai as genai


class Gemini:
    def __init__(self, GOOGLE_API_KEY: str):
        if not GOOGLE_API_KEY:
            raise ValueError("Google API key is required for Gemini model")
        if not isinstance(GOOGLE_API_KEY, str):
            raise TypeError("Google API key must be a string")

        super().__init__()

        genai.configure(api_key=GOOGLE_API_KEY)
        self.__gemini = genai.GenerativeModel(
            "models/gemini-2.0-flash-lite",
            generation_config=genai.types.GenerationConfig(
                temperature=0.0, max_output_tokens=1024
            ),
        )

    def generate(self, history: list = []):
        return self.__gemini.start_chat(history=history)
