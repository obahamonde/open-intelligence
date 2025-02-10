import typing as tp
import typing_extensions as tpe
from pydantic import BaseModel, Field, computed_field


class Data(BaseModel):
    code: str
    message: str
    param: tp.Optional[str]
    line: tp.Optional[int]


class RequestCounts(BaseModel):
    total: int
    failed: int
    completed: int


class Error(BaseModel):
    object: list[str]
    data: list[Data]
    input_file_id: str
    completion_window: str
    status: str
    output_file_id: str
    error_file_id: str
    created_at: int
    in_progress_at: int
    expires_at: int
    finalizing_at: int
    completed_at: int
    failed_at: int
    expired_at: int
    cancelling_at: int
    cancelled_at: int
    finalized_at: int
    request_counts: RequestCounts
    metadata: dict[str, tp.Any]


class BatchRequest(BaseModel):
    input_file_id: str
    endpoint: str
    completion_window: str
    metadata: dict[str, object]


class CancelBatchRetrieve(BaseModel):
    batch_id: str


class BatchObject(BaseModel):
    id: str
    object: str
    endpoint: str
    errors: list[Error]
