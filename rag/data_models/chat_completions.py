from pydantic import BaseModel


class ChatCompletionsMessage(BaseModel):
    role: str
    content: str


class ChatCompletionsBody(BaseModel):
    model: str = "gpt-4o-2024-08-06"
    temperature: float = 0
    seed: int = 42
    messages: list[ChatCompletionsMessage]
    max_tokens: int = 1000


class ChatCompletionsRequestModel(BaseModel):
    custom_id: str
    method: str = "POST"
    url: str = "/v1/chat/completions"
    body: ChatCompletionsBody
