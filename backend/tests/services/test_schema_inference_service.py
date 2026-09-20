"""
Strict adversarial unit tests for app/services/schema_inference_service.py

CSV -> schema inference is heuristic-heavy, so correctness means:
  1. Name heuristics: keyword-named columns map to the intended type.
  2. Data heuristics: when no name keyword matches, dtype drives the type
     (int -> integer, float -> decimal, bool -> boolean, low-cardinality ->
     category, else string).
  3. Constraint inference: numeric min/max + uniform distribution; date_range
     for dates; category values + weighted distribution; id prefix.
  4. Round-trip integrity: every inferred column dict must build a valid
     ColumnSchema (the inference output feeds straight back into generation).
  5. CSV entry points: empty / header-only inputs raise clear ValueErrors.

TestSuspectedBugs are HYPOTHESES expected to FAIL. Do NOT weaken them; fix the
source or record a signed-off design decision.
"""

import io

import pandas as pd
import pytest

from app.models.schema_models import ColumnSchema
from app.services import schema_inference_service as si


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def infer(series_data, name):
    return si.infer_column_type(pd.Series(series_data), name)


class _UploadStub:
    """Mimics the object passed to infer_schema_from_csv (has a .file attr)."""
    def __init__(self, text):
        self.file = io.StringIO(text)


# ===========================================================================
# infer_id_prefix
# ===========================================================================

class TestInferIdPrefix:

    def test_alpha_prefix_extracted_and_upper(self):
        assert si.infer_id_prefix(pd.Series(["cust001", "cust002"])) == "CUST"

    def test_numeric_only_falls_back_to_ID(self):
        assert si.infer_id_prefix(pd.Series(["12345", "67890"])) == "ID"

    def test_empty_series_falls_back_to_ID(self):
        assert si.infer_id_prefix(pd.Series([], dtype="object")) == "ID"


# ===========================================================================
# Name-based type detection
# ===========================================================================

class TestNameHeuristics:
    @pytest.mark.parametrize("name,expected", [
        ("user_email", "email"),
        ("email_address", "email"),
        ("mobile_phone", "phone"),
        ("phone_number", "phone"),
        ("customer_id", "id"),
        ("id", "id"),
        ("order_date", "date"),
        ("dob", "date"),
        ("total_amount", "currency_amount"),
        ("unit_price", "currency_amount"),
        ("monthly_salary", "currency_amount"),
        ("home_city", "category"),
        ("home_state", "category"),
        ("home_country", "category"),
        ("order_status", "category"),
        ("account_type", "category"),
        ("full_name", "name"),
    ])
    def test_name_keyword_maps_to_type(self, name, expected):
        # Use generic string data so the NAME drives the decision.
        assert infer(["x", "y", "z"], name) == expected


# ===========================================================================
# Data-based type detection (name is neutral)
# ===========================================================================

class TestDataHeuristics:

    def test_integer_dtype(self):
        assert infer([1, 2, 3, 4], "col1") == "integer"

    def test_float_dtype_is_decimal(self):
        assert infer([1.5, 2.5, 3.5], "col1") == "decimal"

    def test_bool_dtype(self):
        assert infer([True, False, True], "col1") == "boolean"

    def test_low_cardinality_becomes_category(self):
        assert infer(["a", "b", "a", "b", "c"], "col1") == "category"

    def test_high_cardinality_strings_are_string(self):
        assert infer([f"txt_{i}" for i in range(50)], "col1") == "string"

    def test_all_null_is_string(self):
        assert infer([None, None, None], "col1") == "string"


# ===========================================================================
# should_mark_unique
# ===========================================================================

class TestShouldMarkUnique:

    @pytest.mark.parametrize("t", ["id", "email", "uuid", "phone"])
    def test_marks_unique_types(self, t):
        assert si.should_mark_unique(pd.Series(["a"]), t, "c") is True

    @pytest.mark.parametrize("t", ["integer", "decimal", "category", "string", "name"])
    def test_non_unique_types(self, t):
        assert si.should_mark_unique(pd.Series(["a"]), t, "c") is False


# ===========================================================================
# Constraint inference (via infer_schema_from_dataframe)
# ===========================================================================

def _column(df, name):
    schema = si.infer_schema_from_dataframe(df)
    for c in schema["columns"]:
        if c["name"] == name:
            return c
    raise AssertionError(f"column {name} not found")


class TestConstraintInference:

    def test_numeric_min_max_and_distribution(self):
        df = pd.DataFrame({"reading": [10, 20, 30]})
        c = _column(df, "reading")
        assert c["type"] == "integer"
        assert c["min"] == 10.0 and c["max"] == 30.0
        assert c["distribution"]["type"] == "uniform"
        assert c["distribution"]["min"] == 10.0 and c["distribution"]["max"] == 30.0

    def test_date_range_distribution(self):
        df = pd.DataFrame({"order_date": ["2020-01-01", "2020-06-15", "2020-12-31"]})
        c = _column(df, "order_date")
        assert c["type"] == "date"
        assert c["distribution"]["type"] == "date_range"
        assert c["distribution"]["start_date"] == "2020-01-01"
        assert c["distribution"]["end_date"] == "2020-12-31"

    def test_category_values_and_weights(self):
        df = pd.DataFrame({"col1": ["x", "y", "x", "x", "y"]})
        c = _column(df, "col1")
        assert c["type"] == "category"
        assert set(c["values"]) == {"x", "y"}
        assert c["distribution"]["type"] == "weighted"
        assert c["distribution"]["weights"]["x"] == 3
        assert c["distribution"]["weights"]["y"] == 2

    def test_id_prefix_inferred(self):
        df = pd.DataFrame({"customer_id": ["CUST001", "CUST002", "CUST003"]})
        c = _column(df, "customer_id")
        assert c["type"] == "id"
        assert c["prefix"] == "CUST"

    def test_required_and_nullable_no_nulls(self):
        df = pd.DataFrame({"reading": [1, 2, 3]})
        c = _column(df, "reading")
        assert c["required"] is True
        assert c["nullable"] is False

    def test_required_and_nullable_with_nulls(self):
        df = pd.DataFrame({"reading": [1, None, 3]})
        c = _column(df, "reading")
        assert c["required"] is False
        assert c["nullable"] is True


# ===========================================================================
# Round-trip: inferred columns must build valid ColumnSchema
# ===========================================================================

class TestRoundTrip:

    def test_inferred_schema_builds_valid_columnschemas(self):
        df = pd.DataFrame({
            "customer_id": ["CUST001", "CUST002", "CUST003", "CUST004"],
            "user_email": ["a@x.com", "b@x.com", "c@x.com", "d@x.com"],
            "reading": [10, 20, 30, 40],
            "score": [1.5, 2.5, 3.5, 4.5],
            "order_status": ["open", "closed", "open", "closed"],
            "order_date": ["2020-01-01", "2020-02-01", "2020-03-01", "2020-04-01"],
        })
        schema = si.infer_schema_from_dataframe(df)
        for col_dict in schema["columns"]:
            # Must not raise ValidationError.
            ColumnSchema(**col_dict)

    def test_schema_metadata_fields(self):
        df = pd.DataFrame({"reading": [1, 2, 3]})
        schema = si.infer_schema_from_dataframe(df)
        assert schema["synthetic_only"] is True
        assert schema["row_count_detected"] == 3
        assert schema["columns_detected"] == 1


# ===========================================================================
# CSV entry points
# ===========================================================================

class TestInferSchemaFromCsv:

    def test_valid_csv(self):
        stub = _UploadStub("reading,order_status\n1,open\n2,closed\n3,open\n")
        schema = si.infer_schema_from_csv(stub)
        assert schema["row_count_detected"] == 3
        assert schema["columns_detected"] == 2

    def test_empty_csv_raises(self):
        stub = _UploadStub("")
        with pytest.raises(ValueError):
            si.infer_schema_from_csv(stub)

    def test_header_only_raises(self):
        stub = _UploadStub("a,b\n")
        with pytest.raises(ValueError):
            si.infer_schema_from_csv(stub)


# ===========================================================================
# SUSPECTED BUGS -- expected to FAIL. Do NOT weaken.
# ===========================================================================

class TestSuspectedBugs:

    def test_bug_update_substring_forces_date_on_integer_column(self):
        """Substring false-positive. 'date' is a substring of 'up-DATE'-style
        names, so a clearly-integer column named 'update_count' is inferred as
        'date' because the name heuristic uses `'date' in name` without word
        boundaries. The obvious integer data is ignored."""
        inferred = infer([1, 2, 3, 4, 5], "update_count")
        assert inferred == "integer", (
            f"'update_count' (integer data) inferred as '{inferred}' due to "
            f"substring match of 'date' inside 'update'"
        )

    def test_bug_last_update_not_date(self):
        """A 'last_update' column holding categorical text should not become a
        date purely because 'update' contains the substring 'date'."""
        inferred = infer(["active", "inactive", "active"], "last_update")
        assert inferred != "date", (
            "'last_update' misclassified as date via substring match"
        )

    def test_bug_username_substring_forces_name(self):
        """'name' is a substring of 'username'. A high-cardinality username
        column (which should be a plain string) is inferred as a person 'name'
        type. Borderline -- if you intend any *name* column to map to name,
        this is a design choice; otherwise it's a false positive."""
        inferred = infer([f"user_{i}" for i in range(40)], "username")
        assert inferred != "name", (
            "'username' misclassified as name via substring match"
        )