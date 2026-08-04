"""
Strict adversarial unit tests for app/services/case_value_generation_service.py

This module deliberately produces "bad" data for each case label. So correctness
means three things:
  1. Structure: every generator returns a 2-tuple (value, reason_dict), and each
     reason has column/label/reason with column == column.name.
  2. Violation correctness: a "range_violation" value must ACTUALLY exceed the
     range; a "length_violation" must ACTUALLY break the length; "null_case" must
     be None; boundary values must sit exactly on the boundary; etc.
  3. Label integrity: the returned reason label must match the REQUESTED case
     type. If a range violation is requested, the row must not come back labeled
     "invalid_case".

TestSuspectedBugs at the bottom are HYPOTHESES expected to FAIL against the
current source. Each failure = a defect to fix in the SOURCE (or a documented
design decision you sign off on) -- never fixed by weakening a test.
"""

import re

import pytest

from app.models.schema_models import ColumnSchema, DistributionConfig
from app.utils.constants import CASE_LABELS
from app.services import case_value_generation_service as cg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def col(**kwargs):
    base = {"name": "c", "type": "string"}
    base.update(kwargs)
    return ColumnSchema(**base)


def assert_reason_shape(reason, expected_label, column):
    assert isinstance(reason, dict)
    assert set(reason.keys()) == {"column", "label", "reason"}
    assert reason["column"] == column.name
    assert reason["label"] == expected_label
    assert isinstance(reason["reason"], str) and reason["reason"] != ""
    assert reason["label"] in CASE_LABELS


# ===========================================================================
# build_reason
# ===========================================================================

class TestBuildReason:

    def test_shape(self):
        c = col(name="age", type="integer", min=1, max=10)
        r = cg.build_reason(c, "null_case", "null_value_injected")
        assert r == {"column": "age", "label": "null_case", "reason": "null_value_injected"}


# ===========================================================================
# null_case
# ===========================================================================

class TestNullCase:

    def test_null_value_and_label(self):
        c = col(type="integer", min=1, max=10)
        value, reason = cg.generate_null_case_value(c)
        assert value is None
        assert_reason_shape(reason, "null_case", c)


# ===========================================================================
# range_violation
# ===========================================================================

class TestRangeViolation:

    def test_numeric_with_max_exceeds_max(self):
        c = col(type="integer", min=1, max=10)
        value, reason = cg.generate_range_violation_value(c)
        assert value > 10
        assert_reason_shape(reason, "range_violation_case", c)

    def test_numeric_with_min_only_below_min(self):
        c = col(type="number", min=5)
        value, reason = cg.generate_range_violation_value(c)
        assert value < 5
        assert_reason_shape(reason, "range_violation_case", c)

    def test_numeric_without_bounds_returns_sentinel(self):
        c = col(type="float")
        value, reason = cg.generate_range_violation_value(c)
        assert value == -999999
        assert_reason_shape(reason, "range_violation_case", c)


# ===========================================================================
# length_violation
# ===========================================================================

class TestLengthViolation:

    def test_string_with_max_length_exceeds(self):
        c = col(type="string", max_length=5)
        value, reason = cg.generate_length_violation_value(c)
        assert isinstance(value, str)
        assert len(value) > 5
        assert_reason_shape(reason, "length_violation_case", c)

    def test_string_with_min_length_only_returns_empty(self):
        c = col(type="string", min_length=5)
        value, reason = cg.generate_length_violation_value(c)
        assert value == ""
        assert len(value) < 5
        assert_reason_shape(reason, "length_violation_case", c)

    def test_text_without_length_returns_very_long(self):
        c = col(type="long_text")
        value, reason = cg.generate_length_violation_value(c)
        assert isinstance(value, str)
        assert len(value) >= 100
        assert_reason_shape(reason, "length_violation_case", c)


# ===========================================================================
# format_violation
# ===========================================================================

class TestFormatViolation:

    @pytest.mark.parametrize("dtype,needle", [
        ("email", "invalid-email"),
        ("phone", "abc-phone-123"),
        ("uuid", "invalid-uuid"),
        ("url", "not-a-url"),
        ("ip_address", "999.999.999.999"),
        ("boolean", "not_boolean"),
    ])
    def test_known_type_format_violations(self, dtype, needle):
        c = col(type=dtype)
        value, reason = cg.generate_format_violation_value(c)
        assert value == needle
        assert_reason_shape(reason, "format_violation_case", c)

    def test_date_family_format_violation(self):
        for dtype in ["date", "datetime", "timestamp"]:
            c = col(type=dtype)
            value, reason = cg.generate_format_violation_value(c)
            assert value == "not-a-date"
            assert_reason_shape(reason, "format_violation_case", c)

    def test_generic_fallback_format_violation(self):
        c = col(type="string")
        value, reason = cg.generate_format_violation_value(c)
        assert value == "@@@###INVALID###@@@"
        assert_reason_shape(reason, "format_violation_case", c)


# ===========================================================================
# boundary_case
# ===========================================================================

class TestBoundaryCase:

    def test_numeric_returns_min_boundary(self):
        c = col(type="float", min=3, max=9)
        value, reason = cg.generate_boundary_case_value(c)
        assert value == 3
        assert_reason_shape(reason, "boundary_case", c)

    def test_numeric_max_when_no_min(self):
        c = col(type="float", max=9)
        value, reason = cg.generate_boundary_case_value(c)
        assert value == 9
        assert_reason_shape(reason, "boundary_case", c)

    def test_numeric_zero_when_unbounded(self):
        c = col(type="float")
        value, reason = cg.generate_boundary_case_value(c)
        assert value == 0
        assert_reason_shape(reason, "boundary_case", c)

    def test_string_max_length_exact(self):
        c = col(type="string", max_length=8)
        value, reason = cg.generate_boundary_case_value(c)
        assert value == "A" * 8
        assert len(value) == 8
        assert_reason_shape(reason, "boundary_case", c)

    def test_string_empty_when_no_length(self):
        c = col(type="string")
        value, reason = cg.generate_boundary_case_value(c)
        assert value == ""
        assert_reason_shape(reason, "boundary_case", c)

    def test_category_first_value(self):
        c = col(type="category", values=["red", "green", "blue"])
        value, reason = cg.generate_boundary_case_value(c)
        assert value == "red"
        assert_reason_shape(reason, "boundary_case", c)


# ===========================================================================
# corner_case
# ===========================================================================

class TestCornerCase:

    def test_date_is_leap_day(self):
        c = col(type="date")
        value, reason = cg.generate_corner_case_value(c)
        assert value == "2024-02-29"
        assert_reason_shape(reason, "corner_case", c)

    def test_datetime_is_leap_day(self):
        c = col(type="datetime")
        value, reason = cg.generate_corner_case_value(c)
        assert value == "2024-02-29T23:59:59"
        assert_reason_shape(reason, "corner_case", c)

    def test_category_last_value(self):
        c = col(type="category", values=["red", "green", "blue"])
        value, reason = cg.generate_corner_case_value(c)
        assert value == "blue"
        assert_reason_shape(reason, "corner_case", c)

    def test_boolean_true_corner(self):
        c = col(type="boolean")
        value, reason = cg.generate_corner_case_value(c)
        assert value is True
        assert_reason_shape(reason, "corner_case", c)


# ===========================================================================
# invalid_case
# ===========================================================================

class TestInvalidCase:

    def test_numeric_returns_non_numeric_string(self):
        c = col(type="integer", min=1, max=10)
        value, reason = cg.generate_invalid_case_value(c)
        assert value == "not_a_number"
        assert isinstance(value, str)
        assert_reason_shape(reason, "invalid_case", c)

    def test_category_invalid_member(self):
        c = col(type="category", values=["a", "b"])
        value, reason = cg.generate_invalid_case_value(c)
        assert value == "INVALID_CATEGORY"
        assert value not in c.values
        assert_reason_shape(reason, "invalid_case", c)

    @pytest.mark.parametrize("dtype,expected", [
        ("email", "invalid-email"),
        ("phone", "123"),
        ("uuid", "bad-uuid"),
        ("url", "bad-url"),
        ("ip_address", "999.999.999.999"),
        ("boolean", "not_boolean"),
    ])
    def test_typed_invalids(self, dtype, expected):
        c = col(type=dtype)
        value, reason = cg.generate_invalid_case_value(c)
        assert value == expected
        assert_reason_shape(reason, "invalid_case", c)


# ===========================================================================
# edge_case
# ===========================================================================

class TestEdgeCase:

    def test_nullable_delegates_to_null(self):
        c = col(type="string", nullable=True)
        value, reason = cg.generate_edge_case_value(c)
        assert value is None
        assert_reason_shape(reason, "null_case", c)  # documented: delegates to null

    def test_email_edge_value(self):
        c = col(type="email")
        value, reason = cg.generate_edge_case_value(c)
        assert value == "missing-domain@"
        assert_reason_shape(reason, "edge_case", c)

    def test_phone_edge_value(self):
        c = col(type="phone")
        value, reason = cg.generate_edge_case_value(c)
        assert value == "0000000000"
        assert_reason_shape(reason, "edge_case", c)

    def test_numeric_edge_in_documented_set(self):
        c = col(type="integer", min=1, max=10)
        seen = set()
        for _ in range(200):
            value, reason = cg.generate_edge_case_value(c)
            seen.add(value)
            assert_reason_shape(reason, "edge_case", c)
        assert seen.issubset({0, -1, 999999999})


# ===========================================================================
# duplicate_case
# ===========================================================================

class TestDuplicateCase:

    def test_returns_existing_tracked_value(self):
        c = col(type="string")
        trackers = {"c": {"X", "Y", "Z"}}
        for _ in range(50):
            value, reason = cg.generate_duplicate_case_value(c, trackers)
            assert value in {"X", "Y", "Z"}
            assert_reason_shape(reason, "duplicate_case", c)

    def test_no_tracker_generates_fresh_value(self):
        c = col(type="country")  # deterministic: always "India"
        value, reason = cg.generate_duplicate_case_value(c, {})
        assert value == "India"
        assert_reason_shape(reason, "duplicate_case", c)


# ===========================================================================
# Dispatcher: generate_case_value
# ===========================================================================

class TestDispatcher:

    def test_routes_null_case(self):
        c = col(type="integer", min=1, max=10)
        value, reason = cg.generate_case_value(c, "null_case", 0, {})
        assert value is None
        assert reason["label"] == "null_case"

    def test_normal_fallback_returns_none_reason(self):
        c = col(type="country")
        value, reason = cg.generate_case_value(c, "normal", 0, {})
        assert value == "India"
        assert reason is None

    def test_unknown_case_type_falls_back_to_normal(self):
        c = col(type="country")
        value, reason = cg.generate_case_value(c, "totally_unknown", 3, {})
        assert value == "India"
        assert reason is None

    @pytest.mark.parametrize("case_type", [
        "null_case", "range_violation_case", "length_violation_case",
        "format_violation_case", "boundary_case", "corner_case",
        "invalid_case", "edge_case", "duplicate_case",
    ])
    def test_every_case_returns_tuple_with_valid_label(self, case_type):
        # Use a well-typed string column so most branches behave "natively".
        c = col(type="string", min_length=2, max_length=12)
        value, reason = cg.generate_case_value(c, case_type, 0, {"c": {"seed"}})
        assert reason is not None
        assert reason["label"] in CASE_LABELS


# ===========================================================================
# SUSPECTED BUGS -- expected to FAIL against current source.
# Do NOT weaken. Fix source or record a signed-off design decision.
# ===========================================================================

class TestSuspectedBugs:

    def test_bug_range_violation_on_string_keeps_requested_label(self):
        """Label-integrity bug. Requesting a range violation for a non-numeric
        column silently delegates to invalid_case, so the row comes back labeled
        'invalid_case' instead of 'range_violation_case'. The __case_labels
        metadata will then disagree with why the row was actually selected."""
        c = col(type="string")
        value, reason = cg.generate_case_value(c, "range_violation_case", 0, {})
        assert reason["label"] == "range_violation_case", (
            f"expected range_violation_case, got '{reason['label']}'"
        )

    def test_bug_length_violation_on_numeric_keeps_requested_label(self):
        """Same label-integrity issue for length violations requested on a
        numeric column (delegates to invalid_case)."""
        c = col(type="integer", min=1, max=10)
        value, reason = cg.generate_case_value(c, "length_violation_case", 0, {})
        assert reason["label"] == "length_violation_case", (
            f"expected length_violation_case, got '{reason['label']}'"
        )

    def test_bug_edge_case_on_uuid_keeps_requested_label(self):
        """edge_case for a uuid column falls through to invalid_case, so an
        'edge_case' request is mislabeled as 'invalid_case'."""
        c = col(type="uuid")
        value, reason = cg.generate_case_value(c, "edge_case", 0, {})
        assert reason["label"] == "edge_case", (
            f"expected edge_case, got '{reason['label']}'"
        )

    def test_bug_integer_boundary_returns_int_not_float(self):
        """Type-integrity bug. boundary_case for an integer column returns
        column.min, which is stored as a float (e.g. 5.0). The normal generator
        returns a real int, so the same column ends up mixing 5 and 5.0 across
        rows -- a data-quality inconsistency in the exported column."""
        c = col(type="integer", min=5, max=10)
        value, reason = cg.generate_boundary_case_value(c)
        assert isinstance(value, int) and not isinstance(value, bool), (
            f"integer boundary returned {type(value).__name__} ({value!r})"
        )

        def test_corner_case_numeric_stays_within_declared_bounds(self):
            """After Option A fix: numeric corner values stay inside the declared
            range. Out-of-range weirdness is the job of range_violation_case."""
            c = col(type="integer", min=100, max=200)
            for _ in range(300):
                value, reason = cg.generate_corner_case_value(c)
                assert 100 <= value <= 200
                assert isinstance(value, int) and not isinstance(value, bool)
                assert reason["label"] == "corner_case"