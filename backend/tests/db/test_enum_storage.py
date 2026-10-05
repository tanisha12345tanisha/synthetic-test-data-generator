from sqlalchemy import Enum, inspect

from app.db.models import (
    AuditEvent, Dataset, DatasetShare, GenerationOutput, GenerationRun,
    SchemaVersion, User,
)


def enum_values(model, column_name):
    column = inspect(model).columns[column_name]
    assert isinstance(column.type, Enum)
    return set(column.type.enums)


def test_all_native_enums_store_public_lowercase_values():
    assert enum_values(User, "role") == {"user", "admin"}
    assert enum_values(User, "status") == {"active", "disabled"}
    assert enum_values(Dataset, "dataset_type") == {"single_table", "connected_tables"}
    assert enum_values(Dataset, "input_mode") == {"manual", "csv", "database", "json", "template"}
    assert enum_values(Dataset, "status") == {"draft", "active", "archived"}
    assert enum_values(DatasetShare, "permission") == {"viewer", "editor"}
    assert enum_values(SchemaVersion, "trigger") == {"manual_save", "generation", "import", "restore"}
    assert enum_values(GenerationRun, "status") == {"queued", "running", "completed", "failed", "cancelled"}
    assert enum_values(GenerationOutput, "output_format") == {"csv", "json", "psv", "zip"}
    assert enum_values(AuditEvent, "result") == {"success", "failure"}
