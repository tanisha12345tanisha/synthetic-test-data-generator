import pytest
from pydantic import ValidationError
from app.schemas.dataset_storage import DatasetCreate, DatasetUpdate, ShareCreate
from app.db.models import SharePermission

def test_dataset_create_defaults_to_empty_schema():
    item=DatasetCreate(name="Customers")
    assert item.schema_document == {}

def test_dataset_name_cannot_be_empty():
    with pytest.raises(ValidationError): DatasetCreate(name="")

def test_dataset_update_allows_schema_document():
    update=DatasetUpdate(schema_document={"columns":[{"name":"id"}]})
    assert update.schema_document["columns"][0]["name"] == "id"

def test_share_permission_is_validated():
    share=ShareCreate(email="viewer@example.com",permission=SharePermission.VIEWER)
    assert share.permission == SharePermission.VIEWER
