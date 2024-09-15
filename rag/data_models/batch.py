from typing import Any, Dict, Optional

from pydantic import BaseModel


class BatchRequestMetadata(BaseModel):
    description: str


class BatchRequestModel(BaseModel):
    input_file_id: str
    endpoint: str = "/v1/chat/completions"
    completion_window: str = "24h"
    metadata: Optional[BatchRequestMetadata]


class BatchResponseCounts(BaseModel):
    total: int
    completed: int
    failed: int


class BatchResponseModel(BaseModel):
    id: str
    object: str
    endpoint: str
    errors: Optional[Any]
    input_file_id: str
    completion_window: str
    status: str
    output_file_id: Optional[str]
    error_file_id: Optional[str]
    created_at: int
    in_progress_at: Optional[int]
    expires_at: int
    completed_at: Optional[int]
    failed_at: Optional[int]
    expired_at: Optional[int]
    request_counts: BatchResponseCounts
    metadata: Optional[Dict[str, Any]]


class BatchOutputChoice(BaseModel):
    index: int
    message: Dict[str, Any]
    logprobs: Optional[Any]
    finish_reason: str


class BatchOutputUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class BatchOutputBody(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list[BatchOutputChoice]
    usage: BatchOutputUsage
    system_fingerprint: str


class BatchOutputResponse(BaseModel):
    status_code: int
    request_id: str
    body: BatchOutputBody
    error: Optional[Any]


class BatchOutputModel(BaseModel):
    id: str
    custom_id: str
    response: BatchOutputResponse
