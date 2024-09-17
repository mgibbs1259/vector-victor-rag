from typing import Any, Dict, Optional

from pydantic import BaseModel


class BatchRequestMetadata(BaseModel):
    description: str


class BatchRequestModel(BaseModel):
    input_file_id: str
    endpoint: str
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
