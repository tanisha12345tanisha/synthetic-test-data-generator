import pytest
from app.services.connected_generation_service import RelationshipValidationError, generate_connected_dataset, topological_table_order

def schema():return {"tables":[{"name":"customers","row_count":3,"columns":[{"name":"id","type":"integer","primary_key":True}]},{"name":"orders","row_count":6,"columns":[{"name":"id","type":"integer","primary_key":True},{"name":"customer_id","type":"integer","foreign_key":True}]}],"relationships":[{"name":"customer_orders","parent_table":"customers","parent_key":"id","child_table":"orders","child_key":"customer_id","cardinality":"one_to_many"}]}
def test_parent_before_child():assert topological_table_order(schema())==["customers","orders"]
def test_connected_generation_has_no_orphans():
 tables,report=generate_connected_dataset(schema(),42);assert report["valid"];assert len(tables["orders"])==6
def test_cycle_rejected():
 item=schema();item["relationships"].append({"parent_table":"orders","parent_key":"id","child_table":"customers","child_key":"order_id","cardinality":"one_to_many"})
 with pytest.raises(RelationshipValidationError):topological_table_order(item)


def test_many_to_many_creates_junction_rows():
    item={"tables":[{"name":"users","row_count":2,"columns":[{"name":"id","type":"integer","primary_key":True}]},{"name":"roles","row_count":2,"columns":[{"name":"id","type":"integer","primary_key":True}]}],"relationships":[{"name":"user_roles","parent_table":"users","parent_key":"id","child_table":"roles","child_key":"id","cardinality":"many_to_many","junction_table":"user_roles"}]}
    tables,report=generate_connected_dataset(item,1)
    assert len(tables["user_roles"])==2
    assert report["valid"]
