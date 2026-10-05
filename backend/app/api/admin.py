from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.db.models import AuditEvent, AuditResult, SystemLimit, User, UserRole, UserStatus
from app.db.session import get_database_session
from app.schemas.admin import (
    AdminSummaryResponse,
    AdminUserResponse,
    AdminUserUpdate,
    AuditEventResponse,
    SystemLimitResponse,
    SystemLimitUpdate,
)
from app.services.admin_service import AdminService


router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/summary", response_model=AdminSummaryResponse)
async def summary(
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
):
    return await AdminService(session, admin).summary()


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    search: str | None = None,
    role: UserRole | None = None,
    status: UserStatus | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    statement = select(User)
    if search:
        query = f"%{search.strip().lower()}%"
        statement = statement.where(
            User.normalized_email.ilike(query) | User.display_name.ilike(query)
        )
    if role is not None:
        statement = statement.where(User.role == role)
    if status is not None:
        statement = statement.where(User.status == status)
    result = await session.execute(
        statement.order_by(User.created_at.desc()).offset(offset).limit(limit)
    )
    return result.scalars().all()


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: UUID,
    payload: AdminUserUpdate,
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return await AdminService(session, admin).update_user(
        user,
        role=payload.role,
        status=payload.status,
    )


@router.get("/limits", response_model=list[SystemLimitResponse])
async def list_limits(
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
):
    return await AdminService(session, _admin).ensure_default_limits()


@router.put("/limits/{key}", response_model=SystemLimitResponse)
async def set_limit(
    key: str,
    payload: SystemLimitUpdate,
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
):
    if payload.key != key:
        raise HTTPException(status_code=400, detail="Path and payload limit keys must match.")
    return await AdminService(session, admin).set_limit(payload)


@router.get("/audit-events", response_model=list[AuditEventResponse])
async def list_audit_events(
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    action: str | None = None,
    result: AuditResult | None = None,
    actor_id: UUID | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=250),
):
    statement = select(AuditEvent)
    if action:
        statement = statement.where(AuditEvent.action.ilike(f"%{action.strip()}%"))
    if result is not None:
        statement = statement.where(AuditEvent.result == result)
    if actor_id is not None:
        statement = statement.where(AuditEvent.actor_id == actor_id)
    result_rows = await session.execute(
        statement.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit)
    )
    return result_rows.scalars().all()
