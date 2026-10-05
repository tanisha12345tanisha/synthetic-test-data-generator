import pytest
from pydantic import ValidationError
from app.schemas.auth import RegistrationRequest, ResetPasswordRequest

def test_registration_requires_matching_passwords():
    with pytest.raises(ValidationError):
        RegistrationRequest(display_name="Test User", email="test@example.com", password="StrongPassword1!", confirm_password="different")

def test_reset_requires_matching_passwords():
    with pytest.raises(ValidationError):
        ResetPasswordRequest(token="x" * 64, password="StrongPassword1!", confirm_password="different")
