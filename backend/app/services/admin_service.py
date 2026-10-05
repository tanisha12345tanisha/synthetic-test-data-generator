from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AuditEvent,
    AuditResult,
    Dataset,
    SystemLimit,
    User,
    UserRole,
    UserStatus,
)
from app.schemas.admin import AdminSummaryResponse, SystemLimitUpdate


DEFAULT_LIMITS = (
    ("maximum_rows_per_table", 10000, "rows"),
    ("maximum_total_rows_per_dataset", 50000, "rows"),
    ("maximum_tables_per_dataset", 5, "tables"),
    ("generated_file_retention_hours", 24, "hours"),
    (
        "connectors_enabled",
        {
            "postgresql": False,
            "mysql": False,
            "sql_server": False,
            "oracle": False,
        },
        None,
    ),
)


LIMIT_RULES = {
    "maximum_rows_per_table": (int, 1, 1_000_000),
    "maximum_total_rows_per_dataset": (int, 1, 5_000_000),
    "maximum_tables_per_dataset": (int, 1, 100),
    "generated_file_retention_hours": (int, 1, 8760),
    "connectors_enabled": (dict, None, None),
}


class AdminService:
    def __init__(self, session: AsyncSession, actor: User) -> None:
        self.session = session
        self.actor = actor

    def audit(
        self,
        action: str,
        *,
        target_type: str | None = None,
        target_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.session.add(
            AuditEvent(
                actor_id=self.actor.id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                result=AuditResult.SUCCESS,
                safe_metadata=metadata,
                timestamp=datetime.now(UTC),
            )
        )

    async def update_user(
        self,
        user: User,
        *,
        role: UserRole | None,
        status: UserStatus | None,
    ) -> User:
        if user.id == self.actor.id and (
            (role is not None and role != UserRole.ADMIN)
            or (status is not None and status != UserStatus.ACTIVE)
        ):
            raise HTTPException(
                status_code=400,
                detail="Administrators cannot demote or disable their own account.",
            )

        changes: dict[str, str] = {}
        if role is not None and role != user.role:
            changes["role"] = role.value
            user.role = role
        if status is not None and status != user.status:
            changes["status"] = status.value
            user.status = status

        if changes:
            self.audit(
                "admin.user.updated",
                target_type="user",
                target_id=user.id,
                metadata=changes,
            )
            await self.session.commit()
            await self.session.refresh(user)
        return user

    @staticmethod
    def validate_limit(payload: SystemLimitUpdate) -> Any:
        rule = LIMIT_RULES.get(payload.key)
        if rule is None:
            raise HTTPException(status_code=400, detail="Unsupported system limit key.")
        expected_type, minimum, maximum = rule
        if not isinstance(payload.value, expected_type) or isinstance(payload.value, bool):
            raise HTTPException(status_code=400, detail="Invalid system limit value type.")
        if expected_type is int and not minimum <= payload.value <= maximum:
            raise HTTPException(status_code=400, detail="System limit value is out of range.")
        if payload.key == "connectors_enabled":
            if not all(
                isinstance(key, str) and isinstance(value, bool)
                for key, value in payload.value.items()
            ):
                raise HTTPException(status_code=400, detail="Connector settings must contain boolean values.")
        return payload.value

    async def set_limit(self, payload: SystemLimitUpdate) -> SystemLimit:
        value = self.validate_limit(payload)
        result = await self.session.execute(
            select(SystemLimit).where(SystemLimit.key == payload.key)
        )
        item = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if item is None:
            item = SystemLimit(
                key=payload.key,
                value=value,
                unit=payload.unit,
                effective_at=now,
                updated_by=self.actor.id,
            )
            self.session.add(item)
        else:
            item.value = value
            item.unit = payload.unit
            item.effective_at = now
            item.updated_by = self.actor.id
        self.audit(
            "admin.system_limit.updated",
            target_type="system_limit",
            target_id=item.id,
            metadata={"key": payload.key, "value": value, "unit": payload.unit},
        )
        await self.session.commit()
        await self.session.refresh(item)
        return item


    async def ensure_default_limits(self) -> list[SystemLimit]:
        existing = (
            await self.session.execute(
                select(SystemLimit).order_by(SystemLimit.key)
            )
        ).scalars().all()
        if existing:
            return list(existing)

        items: list[SystemLimit] = []
        now = datetime.now(UTC)
        for key, value, unit in DEFAULT_LIMITS:
            item = SystemLimit(
                key=key,
                value=value,
                unit=unit,
                effective_at=now,
                updated_by=self.actor.id,
            )
            self.session.add(item)
            items.append(item)
        self.audit(
            "admin.system_limits.initialized",
            target_type="system_limit",
            metadata={"keys": [item.key for item in items]},
        )
        await self.session.commit()
        for item in items:
            await self.session.refresh(item)
        return sorted(items, key=lambda item: item.key)

    async def summary(self) -> AdminSummaryResponse:
        users = await self.session.scalar(select(func.count()).select_from(User))
        active_users = await self.session.scalar(
            select(func.count()).select_from(User).where(User.status == UserStatus.ACTIVE)
        )
        datasets = await self.session.scalar(select(func.count()).select_from(Dataset))
        audit_events = await self.session.scalar(select(func.count()).select_from(AuditEvent))
        return AdminSummaryResponse(
            users=int(users or 0),
            active_users=int(active_users or 0),
            datasets=int(datasets or 0),
            audit_events=int(audit_events or 0),
        )
