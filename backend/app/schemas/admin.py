from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models import AuditResult, UserRole, UserStatus


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    display_name: str
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    last_login_at: datetime | None
    created_at: datetime


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    status: UserStatus | None = None

    @model_validator(mode="after")
    def require_change(self):
        if self.role is None and self.status is None:
            raise ValueError("At least one user field must be supplied.")
        return self


class SystemLimitUpdate(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    value: Any
    unit: str | None = Field(default=None, max_length=50)


class SystemLimitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    key: str
    value: Any
    unit: str | None
    effective_at: datetime
    updated_by: UUID
    updated_at: datetime


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    actor_id: UUID | None
    action: str
    target_type: str | None
    target_id: UUID | None
    result: AuditResult
    safe_metadata: dict | None
    timestamp: datetime


class AdminSummaryResponse(BaseModel):
    users: int
    active_users: int
    datasets: int
    audit_events: int
