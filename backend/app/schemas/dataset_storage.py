from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.db.models import DatasetStatus, DatasetType, InputMode, SchemaVersionTrigger, SharePermission

class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    dataset_type: DatasetType = DatasetType.SINGLE_TABLE
    input_mode: InputMode = InputMode.MANUAL
    schema_document: dict = Field(default_factory=dict)

class DatasetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    status: DatasetStatus | None = None
    schema_document: dict | None = None

class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    dataset_type: DatasetType
    input_mode: InputMode
    status: DatasetStatus
    draft_schema_document: dict
    current_draft_revision: int
    created_at: datetime
    updated_at: datetime
    permission: SharePermission | None = None

class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    offset: int
    limit: int

class VersionCreate(BaseModel):
    trigger: SchemaVersionTrigger = SchemaVersionTrigger.MANUAL_SAVE

class SchemaVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    dataset_id: UUID
    version_number: int
    trigger: SchemaVersionTrigger
    schema_document: dict
    created_by: UUID
    restored_from_version_id: UUID | None
    created_at: datetime

class ShareCreate(BaseModel):
    email: EmailStr
    permission: SharePermission

class ShareResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: EmailStr
    display_name: str
    permission: SharePermission
    created_at: datetime
