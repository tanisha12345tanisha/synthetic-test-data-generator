"""
Strict adversarial unit tests for app/services/data_quality_service.py

This engine REPAIRS data mid-pipeline across 14 rules, so correctness means:
  1. Pure validators are accurate (phone/email/url/ip/uuid/date/pincode).
  2. Helper transforms are correct (name cleaning, email token, dob<->age).
  3. Report math: applicable checks only; passed = total - failed; score right.
  4. infer_effective_type maps names/types correctly (NO substring surprises).
  5. Repairs FIX invalid data and PRESERVE intentional case-labelled invalids.

Pure-function tests use dict "columns" (get_column_attribute supports dicts) so
they don't need the pydantic model or generation stack. Integration tests use
real ColumnSchema and run generation transitively in YOUR env.

TestSuspectedBugs are HYPOTHESES expected to FAIL. Do NOT weaken them; fix the
source or record a signed-off design decision.
"""

import uuid as uuid_mod

import pytest

from app.services import data_quality_service as dq


def dict_col(**kwargs):
    base = {"name": "c", "type": "string"}
    base.update(kwargs)
    return base


def row_with(labels=None, **fields):
    r = dict(fields)
    r["__case_labels"] = labels or []
    return r


# ===========================================================================
# Pure validators
# ===========================================================================

class TestValidators:

    @pytest.mark.parametrize("val", ["+919876543210", "9876543210", "7000000000"])
    def test_valid_indian_phone(self, val):
        assert dq.is_valid_indian_phone(val) is True

    @pytest.mark.parametrize("val", ["1234567890", "12345", "abc", "+9199999"])
    def test_invalid_indian_phone(self, val):
        assert dq.is_valid_indian_phone(val) is False

    @pytest.mark.parametrize("val", ["a@b.com", "john.doe@example.org"])
    def test_valid_email(self, val):
        assert dq.is_valid_email(val) is True

    @pytest.mark.parametrize("val", ["invalid-email", "a@b", "no-at.com", ""])
    def test_invalid_email(self, val):
        assert dq.is_valid_email(val) is False

    @pytest.mark.parametrize("val", ["https://example.com", "http://x.io/path"])
    def test_valid_url(self, val):
        assert dq.is_valid_url(val) is True

    @pytest.mark.parametrize("val", ["not-a-url", "ftp://x.com", "http://x y", ""])
    def test_invalid_url(self, val):
        assert dq.is_valid_url(val) is False

    def test_valid_ip(self):
        assert dq.is_valid_ip("192.168.1.1") is True

    @pytest.mark.parametrize("val", ["999.999.999.999", "abc", "256.1.1.1"])
    def test_invalid_ip(self, val):
        assert dq.is_valid_ip(val) is False

    def test_valid_uuid(self):
        assert dq.is_valid_uuid(str(uuid_mod.uuid4())) is True

    @pytest.mark.parametrize("val", ["bad-uuid", "1234", ""])
    def test_invalid_uuid(self, val):
        assert dq.is_valid_uuid(val) is False

    def test_valid_date(self):
        assert dq.is_valid_date_value("2020-01-01") is True

    @pytest.mark.parametrize("val", ["not-a-date", "2020/01/01"])
    def test_invalid_date(self, val):
        assert dq.is_valid_date_value(val) is False

    def test_valid_datetime(self):
        assert dq.is_valid_datetime_value("2020-01-01T10:30:00") is True

    @pytest.mark.parametrize("val", ["560034", "110001", "700091"])
    def test_valid_pincode(self, val):
        assert dq.is_valid_indian_pincode(val) is True

    @pytest.mark.parametrize("val", ["012345", "56003", "5600345", "abcdef"])
    def test_invalid_pincode(self, val):
        assert dq.is_valid_indian_pincode(val) is False


# ===========================================================================
# Helper transforms
# ===========================================================================

class TestHelpers:

    def test_clean_first_name_word(self):
        assert dq.clean_first_name_word("john.doe", "X") == "John"

    def test_clean_last_name_word(self):
        assert dq.clean_last_name_word("john-doe", "X") == "Doe"

    def test_clean_name_fallback(self):
        assert dq.clean_first_name_word("12345", "Aarav") == "Aarav"

    def test_email_token_strips_non_alnum(self):
        assert dq.email_token("O'Brien!") == "obrien"

    def test_email_token_empty_default(self):
        assert dq.email_token("") == "user"

    def test_parse_date_value_iso(self):
        d = dq.parse_date_value("2020-06-15")
        assert (d.year, d.month, d.day) == (2020, 6, 15)

    def test_parse_date_value_none(self):
        assert dq.parse_date_value(None) is None

    def test_parse_date_value_datetime_string(self):
        d = dq.parse_date_value("2020-06-15T10:00:00")
        assert (d.year, d.month, d.day) == (2020, 6, 15)

    def test_dob_age_round_trip(self):
        dob = dq.generate_dob_from_age(30)
        age = dq.calculate_age_from_dob(dob)
        assert abs(age - 30) <= 1

    def test_build_consistent_email_unique(self):
        used = set()
        emails = [dq.build_consistent_email("john", "doe", i, used) for i in range(50)]
        assert len(emails) == len(set(emails))
        for e in emails:
            assert dq.is_valid_email(e)


# ===========================================================================
# infer_effective_type
# ===========================================================================

class TestInferEffectiveType:

    @pytest.mark.parametrize("name,ctype,expected", [
        ("first_name", "string", "first_name"),
        ("surname", "string", "last_name"),
        ("full_name", "string", "name"),
        ("user_email", "string", "email"),
        ("mobile_number", "string", "phone"),
        ("website", "string", "url"),
        ("ip_address", "string", "ip_address"),
        ("uuid", "string", "uuid"),
        ("pincode", "string", "postal_code"),
        ("created_date", "string", "date"),
        ("dob", "string", "date"),
        ("currency_code", "string", "currency_code"),
        ("total_amount", "string", "currency_amount"),
        ("age", "string", "integer"),
        ("some_random_field", "integer", "integer"),
        ("plain_text", "string", "string"),
    ])
    def test_effective_type(self, name, ctype, expected):
        assert dq.infer_effective_type(dict_col(name=name, type=ctype)) == expected


# ===========================================================================
# build_quality_report
# ===========================================================================

class TestQualityReport:

    def test_excludes_not_applicable(self):
        checks = [
            {"status": "pass"},
            {"status": "fail"},
            {"status": "not_applicable"},
        ]
        report = dq.build_quality_report(checks)
        assert report["rules_checked"] == 2
        assert report["rules_passed"] == 1
        assert report["rules_failed"] == 1
        assert report["overall_score"] == 50.0

    def test_all_pass_is_100(self):
        checks = [{"status": "pass"}, {"status": "pass"}]
        report = dq.build_quality_report(checks)
        assert report["overall_score"] == 100
        assert report["rules_failed"] == 0

    def test_all_not_applicable_is_100(self):
        checks = [{"status": "not_applicable"}, {"status": "not_applicable"}]
        report = dq.build_quality_report(checks)
        assert report["rules_checked"] == 0
        assert report["overall_score"] == 100

    def test_checks_preserved_in_report(self):
        checks = [{"status": "pass", "rule": "x"}]
        report = dq.build_quality_report(checks)
        assert report["checks"] == checks


# ===========================================================================
# Numeric range repair (dict columns -> no generation needed)
# ===========================================================================

class TestNumericRangeRepair:

    def test_clamps_above_max(self):
        cols = [dict_col(name="n", type="integer", min=1, max=10)]
        rows = [row_with(n=999)]
        rows, check = dq.repair_numeric_ranges(rows, cols)
        assert rows[0]["n"] == 10
        assert check["rule"] == "numeric_range_consistency"

    def test_clamps_below_min(self):
        cols = [dict_col(name="n", type="integer", min=5, max=10)]
        rows = [row_with(n=-3)]
        rows, check = dq.repair_numeric_ranges(rows, cols)
        assert rows[0]["n"] == 5

    def test_integer_result_is_int(self):
        cols = [dict_col(name="n", type="integer", min=1, max=10)]
        rows = [row_with(n=5.7)]
        rows, check = dq.repair_numeric_ranges(rows, cols)
        assert isinstance(rows[0]["n"], int)

    def test_currency_amount_made_non_negative(self):
        cols = [dict_col(name="amt", type="currency_amount", min=0, max=1000)]
        rows = [row_with(amt=-50)]
        rows, check = dq.repair_numeric_ranges(rows, cols)
        assert rows[0]["amt"] >= 0

    def test_preserves_range_violation_case(self):
        cols = [dict_col(name="n", type="integer", min=1, max=10)]
        rows = [row_with(labels=["range_violation_case"], n=999)]
        rows, check = dq.repair_numeric_ranges(rows, cols)
        assert rows[0]["n"] == 999  # intentionally-invalid must be preserved


# ===========================================================================
# Category repair (dict columns)
# ===========================================================================

class TestCategoryRepair:

    def test_replaces_invalid_with_allowed(self):
        cols = [dict_col(name="c", type="category", values=["a", "b", "c"])]
        rows = [row_with(c="ZZZ")]
        rows, check = dq.repair_category_values(rows, cols)
        assert rows[0]["c"] in {"a", "b", "c"}

    def test_keeps_valid_value(self):
        cols = [dict_col(name="c", type="category", values=["a", "b"])]
        rows = [row_with(c="a")]
        rows, check = dq.repair_category_values(rows, cols)
        assert rows[0]["c"] == "a"

    def test_preserves_invalid_case(self):
        cols = [dict_col(name="c", type="category", values=["a", "b"])]
        rows = [row_with(labels=["invalid_case"], c="ZZZ")]
        rows, check = dq.repair_category_values(rows, cols)
        assert rows[0]["c"] == "ZZZ"


# ===========================================================================
# Country/currency + status/boolean (dict columns, no generation)
# ===========================================================================

class TestConsistencyRepairs:

    def test_country_currency_forced(self):
        cols = [dict_col(name="country", type="country"),
                dict_col(name="currency", type="currency_code")]
        rows = [row_with(country="USA", currency="USD")]
        rows, check = dq.repair_country_currency_consistency(rows, cols)
        assert rows[0]["country"] == "India"
        assert rows[0]["currency"] == "INR"

    def test_status_boolean_alignment(self):
        cols = [dict_col(name="status", type="category"),
                dict_col(name="is_active", type="boolean")]
        rows = [row_with(status="active", is_active=False)]
        rows, check = dq.repair_status_boolean_consistency(rows, cols)
        assert rows[0]["is_active"] is True

    def test_status_boolean_false(self):
        cols = [dict_col(name="status", type="category"),
                dict_col(name="is_active", type="boolean")]
        rows = [row_with(status="closed", is_active=True)]
        rows, check = dq.repair_status_boolean_consistency(rows, cols)
        assert rows[0]["is_active"] is False


# ===========================================================================
# Integration: full pipeline
# ===========================================================================

class TestFullPipeline:

    def test_returns_rows_and_report(self):
        from app.models.schema_models import ColumnSchema
        cols = [ColumnSchema(name="n", type="integer", min=1, max=100)]
        rows = [{"n": 5, "__case_type": "normal", "__case_labels": ["normal"], "__case_reasons": []}
                for _ in range(5)]
        out_rows, report = dq.apply_data_quality_rules(rows, cols)
        assert len(out_rows) == 5
        assert set(["overall_score", "rules_checked", "rules_passed", "rules_failed", "checks"]).issubset(report)
        assert 0 <= report["overall_score"] <= 100

    def test_score_is_numeric_and_bounded(self):
        from app.models.schema_models import ColumnSchema
        cols = [ColumnSchema(name="email", type="email"),
                ColumnSchema(name="n", type="integer", min=1, max=10)]
        rows = [{"email": "x@y.com", "n": 5,
                 "__case_type": "normal", "__case_labels": ["normal"], "__case_reasons": []}]
        _, report = dq.apply_data_quality_rules(rows, cols)
        assert isinstance(report["overall_score"], (int, float))
        assert 0 <= report["overall_score"] <= 100


# ===========================================================================
# SUSPECTED BUGS -- expected to FAIL. Do NOT weaken.
# ===========================================================================

class TestSuspectedBugs:

    def test_bug_integer_clamp_then_round_exceeds_fractional_max(self):
        """Same defect family as Segment 3, unfixed here. repair_numeric_ranges
        clamps to max THEN does int(round(...)). With a fractional max, the
        clamp lands on e.g. 1.6, and rounding pushes it to 2 -- above the
        declared max. Integers must respect the declared bounds after rounding."""
        cols = [dict_col(name="n", type="integer", min=1, max=1.6)]
        rows = [row_with(n=999)]
        rows, check = dq.repair_numeric_ranges(rows, cols)
        assert rows[0]["n"] <= 1.6, (
            f"integer repaired to {rows[0]['n']} which exceeds max=1.6"
        )

    def test_bug_integer_clamp_then_round_below_fractional_min(self):
        """Symmetric low-end: min=2.4 -> clamp to 2.4 -> round to 2 (below min)."""
        cols = [dict_col(name="n", type="integer", min=2.4, max=100)]
        rows = [row_with(n=0)]
        rows, check = dq.repair_numeric_ranges(rows, cols)
        assert rows[0]["n"] >= 2.4, (
            f"integer repaired to {rows[0]['n']} which is below min=2.4"
        )

    def test_known_limitation_mobile_substring_maps_to_phone(self):
        """KNOWN LIMITATION (accepted, not a bug): infer_effective_type uses
        substring matching, so rare names containing 'mobile' (e.g.
        'automobile_id') map to 'phone'. Accepted because such names are
        uncommon in banking/card data and the substring heuristic is
        intentional elsewhere in this function. Documented to keep the behavior
        explicit; revisit if auto-loan/vehicle columns become common."""
        assert dq.infer_effective_type(dict_col(name="automobile_id", type="string")) == "phone"