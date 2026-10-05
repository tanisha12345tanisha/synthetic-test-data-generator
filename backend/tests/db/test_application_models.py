from sqlalchemy import inspect

from app.db.base import Base
from app.db.models import (
    AuditEvent,
    Dataset,
    DatasetShare,
    GenerationOutput,
    GenerationRun,
    QualityReport,
    SchemaVersion,
    SystemLimit,
)


def test_application_tables_are_registered():
    expected = {
        "datasets", "dataset_shares", "schema_versions", "generation_runs",
        "generation_outputs", "quality_reports", "system_limits", "audit_events",
    }
    assert expected.issubset(Base.metadata.tables.keys())


def test_dataset_owner_foreign_key_uses_cascade():
    foreign_key = next(iter(inspect(Dataset).columns.owner_id.foreign_keys))
    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"


def test_dataset_share_is_unique_per_dataset_and_user():
    names = {constraint.name for constraint in DatasetShare.__table__.constraints}
    assert "uq_dataset_shares_dataset_user" in names


def test_schema_version_is_unique_per_dataset_version():
    names = {constraint.name for constraint in SchemaVersion.__table__.constraints}
    assert "uq_schema_versions_dataset_version" in names


def test_generation_run_has_required_foreign_keys():
    mapper = inspect(GenerationRun)
    targets = {
        fk.target_fullname
        for column in mapper.columns
        for fk in column.foreign_keys
    }
    assert targets == {"datasets.id", "schema_versions.id", "users.id"}


def test_generation_output_expires_and_can_be_deleted():
    mapper = inspect(GenerationOutput)
    assert mapper.columns.expires_at.nullable is False
    assert mapper.columns.deleted_at.nullable is True


def test_quality_report_is_one_per_generation():
    generation_column = inspect(QualityReport).columns.generation_id
    assert generation_column.nullable is False
    assert generation_column.unique is True


def test_system_limit_key_is_unique():
    assert inspect(SystemLimit).columns.key.unique is True


def test_audit_event_actor_is_nullable():
    assert inspect(AuditEvent).columns.actor_id.nullable is True


def test_audit_event_uses_safe_metadata_name():
    mapper = inspect(AuditEvent)
    assert "safe_metadata" in mapper.columns
