from enum import StrEnum
from typing import TypeVar


EnumType = TypeVar("EnumType", bound=StrEnum)


def enum_values(enum_class: type[EnumType]) -> list[str]:
    return [member.value for member in enum_class]


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class DatasetType(StrEnum):
    SINGLE_TABLE = "single_table"
    CONNECTED_TABLES = "connected_tables"


class InputMode(StrEnum):
    MANUAL = "manual"
    CSV = "csv"
    DATABASE = "database"
    JSON = "json"
    TEMPLATE = "template"


class DatasetStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class SharePermission(StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"


class SchemaVersionTrigger(StrEnum):
    MANUAL_SAVE = "manual_save"
    GENERATION = "generation"
    IMPORT = "import"
    RESTORE = "restore"


class GenerationStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputFormat(StrEnum):
    CSV = "csv"
    JSON = "json"
    PSV = "psv"
    ZIP = "zip"


class AuditResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
