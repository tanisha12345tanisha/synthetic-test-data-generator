import pytest
from app.services.rules_engine import RuleValidationError, apply_rules, derive_value, evaluate_condition

def test_cross_column_comparison(): assert evaluate_condition({"start":1,"end":2},{"field":"end","operator":"gt","value":{"field":"start"}})
def test_derived_concat(): assert derive_value({"a":"x","b":"y"},{"operation":"concat","separator":"-","operands":[{"field":"a"},{"field":"b"}]})=="x-y"
def test_conditional_derivation(): assert derive_value({"age":20},{"operation":"conditional","condition":{"field":"age","operator":"gte","value":18},"then":{"value":"adult"},"else":{"value":"minor"}})=="adult"
def test_rules_collect_violations():
 result=apply_rules([{"a":2,"b":1}],[{"id":"ordered","kind":"constraint","condition":{"field":"b","operator":"gte","value":{"field":"a"}}}]);assert len(result.violations)==1
def test_unsafe_unknown_operation_rejected():
 with pytest.raises(RuleValidationError):derive_value({}, {"operation":"eval","operands":[]})
