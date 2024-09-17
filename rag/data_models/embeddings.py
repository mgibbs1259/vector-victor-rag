from pydantic import BaseModel


class EmbeddingsBody(BaseModel):
    input: str
    model: str = "text-embedding-3-small"


class EmbeddingsRequestModel(BaseModel):
    custom_id: str
    method: str = "POST"
    url: str = "/v1/embeddings"
    body: EmbeddingsBody
