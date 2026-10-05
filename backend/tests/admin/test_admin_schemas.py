import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.db.models import UserRole, UserStatus
from app.schemas.admin import AdminUserUpdate, SystemLimitUpdate
from app.services.admin_service import AdminService


def test_admin_user_update_requires_a_change():
    with pytest.raises(ValidationError):
        AdminUserUpdate()


def test_admin_user_update_accepts_role_and_status():
    update = AdminUserUpdate(role=UserRole.ADMIN, status=UserStatus.ACTIVE)
    assert update.role == UserRole.ADMIN


def test_integer_system_limit_is_validated():
    payload = SystemLimitUpdate(key="maximum_rows_per_table", value=25000, unit="rows")
    assert AdminService.validate_limit(payload) == 25000


def test_out_of_range_system_limit_is_rejected():
    payload = SystemLimitUpdate(key="maximum_rows_per_table", value=0)
    with pytest.raises(HTTPException):
        AdminService.validate_limit(payload)


def test_connector_flags_must_be_boolean():
    payload = SystemLimitUpdate(key="connectors_enabled", value={"postgresql": "yes"})
    with pytest.raises(HTTPException):
        AdminService.validate_limit(payload)
