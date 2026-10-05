class AuthenticationError(Exception):
    """Base exception for authentication failures."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when supplied credentials cannot be authenticated."""


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid, expired, or has the wrong type."""


class DisabledAccountError(AuthenticationError):
    """Raised when authentication is attempted for a disabled account."""
