from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SUPPORTED_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "is_null", "not_null"}
SUPPORTED_DERIVATIONS = {"copy", "concat", "add", "subtract", "multiply", "divide", "coalesce", "conditional"}


class RuleValidationError(ValueError):
    pass


@dataclass(frozen=True)
class RuleResult:
    rows: list[dict[str, Any]]
    violations: list[dict[str, Any]]


def _value(row: dict[str, Any], operand: Any) -> Any:
    if isinstance(operand, dict) and "field" in operand:
        return row.get(operand["field"])
    return operand.get("value") if isinstance(operand, dict) and "value" in operand else operand


def evaluate_condition(row: dict[str, Any], condition: dict[str, Any]) -> bool:
    operator = condition.get("operator")
    if operator not in SUPPORTED_OPERATORS:
        raise RuleValidationError(f"Unsupported operator: {operator}")
    left = row.get(condition.get("field"))
    right = _value(row, condition.get("value"))
    if operator == "is_null": return left is None
    if operator == "not_null": return left is not None
    if operator == "eq": return left == right
    if operator == "ne": return left != right
    if left is None: return False
    if operator == "gt": return left > right
    if operator == "gte": return left >= right
    if operator == "lt": return left < right
    if operator == "lte": return left <= right
    if operator == "in": return left in right
    return left not in right


def derive_value(row: dict[str, Any], expression: dict[str, Any]) -> Any:
    operation = expression.get("operation")
    if operation not in SUPPORTED_DERIVATIONS:
        raise RuleValidationError(f"Unsupported derivation: {operation}")
    operands = [_value(row, item) for item in expression.get("operands", [])]
    if operation == "copy": return operands[0] if operands else None
    if operation == "concat": return str(expression.get("separator", "")).join("" if value is None else str(value) for value in operands)
    if operation == "coalesce": return next((value for value in operands if value is not None), None)
    if operation == "conditional":
        return _value(row, expression.get("then")) if evaluate_condition(row, expression["condition"]) else _value(row, expression.get("else"))
    if len(operands) < 2: raise RuleValidationError("Arithmetic derivations require two operands.")
    left, right = operands[0], operands[1]
    if operation == "add": return left + right
    if operation == "subtract": return left - right
    if operation == "multiply": return left * right
    if right == 0: raise RuleValidationError("Division by zero is not allowed.")
    return left / right


def apply_rules(rows: list[dict[str, Any]], rules: list[dict[str, Any]]) -> RuleResult:
    output = [dict(row) for row in rows]
    violations: list[dict[str, Any]] = []
    for rule in sorted(rules, key=lambda item: item.get("order", 0)):
        kind = rule.get("kind")
        for index, row in enumerate(output):
            if kind == "derived":
                row[rule["target_field"]] = derive_value(row, rule["expression"])
            elif kind == "constraint" and not evaluate_condition(row, rule["condition"]):
                violations.append({"row_index": index, "rule_id": rule.get("id"), "message": rule.get("message", "Rule failed.")})
            else:
                if kind not in {"derived", "constraint"}: raise RuleValidationError(f"Unsupported rule kind: {kind}")
    return RuleResult(output, violations)
