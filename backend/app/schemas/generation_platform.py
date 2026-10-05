from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.db.models import GenerationStatus, OutputFormat

class GenerationSubmit(BaseModel):
    dataset_id: UUID
    requested_row_total: int = Field(ge=1, le=5_000_000)
    seed: int | None = None
    output_format: OutputFormat = OutputFormat.JSON
    idempotency_key: str = Field(min_length=8, max_length=128)

class GenerationResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: UUID
    dataset_id: UUID
    schema_version_id: UUID
    requested_by: UUID
    seed: int | None
    status: GenerationStatus
    progress_percent: int
    requested_row_total: int
    generated_row_total: int
    current_phase: str
    cancel_requested: bool
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    completed_at: datetime | None

class GenerationOutputResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: UUID
    generation_id: UUID
    output_format: OutputFormat
    size_bytes: int
    checksum_sha256: str
    expires_at: datetime
    deleted_at: datetime | None
