from __future__ import annotations

import random
from typing import Any


class RelationshipValidationError(ValueError):
    pass


def topological_table_order(schema: dict[str, Any]) -> list[str]:
    tables = {table["name"] for table in schema.get("tables", [])}
    graph = {name: set() for name in tables}
    for relationship in schema.get("relationships", []):
        parent, child = relationship["parent_table"], relationship["child_table"]
        if parent not in tables or child not in tables:
            raise RelationshipValidationError("Relationship references an unknown table.")
        if parent == child:
            raise RelationshipValidationError("Self-referencing relationships are not supported.")
        if relationship.get("cardinality") != "many_to_many":
            graph[child].add(parent)
    ordered: list[str] = []
    while graph:
        ready = sorted(name for name, dependencies in graph.items() if not dependencies)
        if not ready: raise RelationshipValidationError("Relationship graph contains a cycle.")
        ordered.extend(ready)
        for name in ready: graph.pop(name)
        for dependencies in graph.values(): dependencies.difference_update(ready)
    return ordered


def _generate_value(column: dict[str, Any], index: int, rng: random.Random) -> Any:
    kind = column.get("type", "string")
    if column.get("primary_key"): return index + 1
    if kind == "integer": return rng.randint(column.get("min", 1), column.get("max", 1000))
    if kind == "boolean": return bool(rng.randint(0, 1))
    if kind == "decimal": return round(rng.uniform(column.get("min", 0), column.get("max", 1000)), 2)
    return f"{column.get('name', 'value')}_{index + 1}"


def generate_connected_dataset(schema: dict[str, Any], seed: int | None = None) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    rng = random.Random(seed)
    definitions = {table["name"]: table for table in schema.get("tables", [])}
    order = topological_table_order(schema)
    result: dict[str, list[dict[str, Any]]] = {}
    for name in order:
        table = definitions[name]
        result[name] = [
            {column["name"]: _generate_value(column, index, rng) for column in table.get("columns", []) if not column.get("foreign_key")}
            for index in range(int(table.get("row_count", 10)))
        ]
    for relationship in schema.get("relationships", []):
        parent_rows = result[relationship["parent_table"]]
        child_rows = result[relationship["child_table"]]
        parent_key = relationship["parent_key"]
        child_key = relationship["child_key"]
        cardinality = relationship.get("cardinality", "one_to_many")
        if not parent_rows: raise RelationshipValidationError("Parent table cannot be empty.")
        if cardinality == "many_to_many":
            junction_name = relationship.get("junction_table")
            if not junction_name:
                raise RelationshipValidationError("Many-to-many relationships require a junction_table.")
            left_key = relationship.get("junction_parent_key", f"{relationship['parent_table']}_id")
            right_key = relationship.get("junction_child_key", f"{relationship['child_table']}_id")
            pairs = []
            for index, child in enumerate(child_rows):
                parent = parent_rows[index % len(parent_rows)]
                pairs.append({left_key: parent[parent_key], right_key: child[child_key]})
            result[junction_name] = pairs
            continue
        if cardinality == "one_to_one" and len(child_rows) > len(parent_rows):
            raise RelationshipValidationError("One-to-one child count exceeds parent count.")
        for index, child in enumerate(child_rows):
            parent = parent_rows[index if cardinality == "one_to_one" else index % len(parent_rows)]
            child[child_key] = parent[parent_key]
    report = validate_referential_integrity(schema, result)
    return result, report


def validate_referential_integrity(schema: dict[str, Any], tables: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    checks=[]; orphan_total=0
    for relationship in schema.get("relationships", []):
        if relationship.get("cardinality") == "many_to_many": continue
        parent_values={row.get(relationship["parent_key"]) for row in tables[relationship["parent_table"]]}
        orphans=[index for index,row in enumerate(tables[relationship["child_table"]]) if row.get(relationship["child_key"]) not in parent_values]
        orphan_total += len(orphans)
        checks.append({"relationship": relationship.get("name"), "orphans": orphans})
    return {"valid": orphan_total == 0, "orphan_count": orphan_total, "checks": checks}
