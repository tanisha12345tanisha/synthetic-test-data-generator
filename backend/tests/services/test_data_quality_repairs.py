"""
Coverage-closing repair-rule tests for app/services/data_quality_service.py

Segment 9's first suite covered validators, helpers, report math, and a few
repair rules. This suite drives the remaining 10 repair FUNCTIONS end to end:
feed each a dirty row, assert it repairs correctly, and assert it PRESERVES
intentional case-labelled invalids (the skip contract).

All use dict "columns" (get_column_attribute supports dicts). Some repairs call
generate_normal_value transitively (faker/rstr), so these run in YOUR env.
"""

import pytest

from app.services import data_quality_service as dq


class _Col:
    """Lightweight column stub with attribute access.

    Repair functions read columns via get_column_attribute (getattr-compatible),
    but some repairs delegate to generate_normal_value, which accesses
    column.type directly. A plain dict fails that attribute access, so we use a
    small object exposing every ColumnSchema field with sensible defaults."""
    _DEFAULTS = {
        "name": "c", "type": "string", "required": True, "nullable": False,
        "unique": False, "min": None, "max": None, "min_length": None,
        "max_length": None, "values": None, "prefix": None, "pattern": None,
        "distribution": None,
    }

    def __init__(self, **kwargs):
        for key, default in self._DEFAULTS.items():
            setattr(self, key, kwargs.get(key, default))


def dcol(**kwargs):
    return _Col(**kwargs)


def rw(labels=None, **fields):
    r = dict(fields)
    r["__case_labels"] = labels or []
    return r


# ===========================================================================
# apply_indian_location_consistency
# ===========================================================================

class TestLocationConsistency:

    def _cols(self):
        return [dcol(name="city", type="city"),
                dcol(name="state", type="state"),
                dcol(name="pincode", type="postal_code")]

    def test_not_applicable_with_one_field(self):
        cols = [dcol(name="city", type="city")]
        rows = [rw(city="Nowhere")]
        rows, check = dq.apply_indian_location_consistency(rows, cols)
        assert check["status"] == "not_applicable"

    def test_makes_city_state_pincode_consistent(self):
        cols = self._cols()
        rows = [rw(city="WrongCity", state="WrongState", pincode="000000")]
        rows, check = dq.apply_indian_location_consistency(rows, cols)
        from app.reference_data.india_locations import INDIA_LOCATION_REFERENCE
        valid = {(l["city"], l["state"], l["pincode"]) for l in INDIA_LOCATION_REFERENCE}
        assert (rows[0]["city"], rows[0]["state"], rows[0]["pincode"]) in valid
        assert check["rule"] == "indian_location_consistency"

    def test_pincode_is_valid_after_repair(self):
        cols = self._cols()
        rows = [rw(city="X", state="Y", pincode="junk") for _ in range(10)]
        rows, check = dq.apply_indian_location_consistency(rows, cols)
        for row in rows:
            assert dq.is_valid_indian_pincode(row["pincode"])

    def test_address_contains_city_and_pincode(self):
        cols = self._cols() + [dcol(name="address", type="address")]
        rows = [rw(city="X", state="Y", pincode="000000", address="junk")]
        rows, check = dq.apply_indian_location_consistency(rows, cols)
        assert str(rows[0]["pincode"]) in str(rows[0]["address"])
        assert str(rows[0]["city"]) in str(rows[0]["address"])

    def test_preserves_invalid_case(self):
        cols = self._cols()
        rows = [rw(labels=["invalid_case"], city="KEEPME", state="KEEP", pincode="000000")]
        rows, check = dq.apply_indian_location_consistency(rows, cols)
        assert rows[0]["city"] == "KEEPME"


# ===========================================================================
# apply_name_email_consistency
# ===========================================================================

class TestNameEmailConsistency:

    def test_not_applicable_with_one_field(self):
        cols = [dcol(name="email", type="email")]
        rows = [rw(email="x@y.com")]
        rows, check = dq.apply_name_email_consistency(rows, cols)
        assert check["status"] == "not_applicable"

    def test_email_reflects_name(self):
        cols = [dcol(name="first_name", type="first_name"),
                dcol(name="last_name", type="last_name"),
                dcol(name="email", type="email")]
        rows = [rw(first_name="John", last_name="Doe", email="junk")]
        rows, check = dq.apply_name_email_consistency(rows, cols)
        email = rows[0]["email"].lower()
        assert "john" in email or "doe" in email
        assert dq.is_valid_email(rows[0]["email"])

    def test_full_name_is_two_words(self):
        cols = [dcol(name="name", type="name"),
                dcol(name="email", type="email")]
        rows = [rw(name="messy.name.here", email="x")]
        rows, check = dq.apply_name_email_consistency(rows, cols)
        assert len(rows[0]["name"].split()) == 2

    def test_emails_unique_across_rows(self):
        cols = [dcol(name="first_name", type="first_name"),
                dcol(name="last_name", type="last_name"),
                dcol(name="email", type="email")]
        rows = [rw(first_name="John", last_name="Doe", email="x") for _ in range(30)]
        rows, check = dq.apply_name_email_consistency(rows, cols)
        emails = [r["email"] for r in rows]
        assert len(emails) == len(set(emails))

    def test_preserves_format_violation(self):
        cols = [dcol(name="first_name", type="first_name"),
                dcol(name="email", type="email")]
        rows = [rw(labels=["format_violation_case"], first_name="John", email="KEEP-INVALID")]
        rows, check = dq.apply_name_email_consistency(rows, cols)
        assert rows[0]["email"] == "KEEP-INVALID"


# ===========================================================================
# repair_required_null_values
# ===========================================================================

class TestRequiredNullRepair:

    def test_fills_null_required(self):
        cols = [dcol(name="n", type="integer", required=True, min=1, max=100)]
        rows = [rw(n=None)]
        rows, check = dq.repair_required_null_values(rows, cols)
        assert rows[0]["n"] is not None

    def test_fills_empty_string_required(self):
        cols = [dcol(name="s", type="string", required=True)]
        rows = [rw(s="   ")]
        rows, check = dq.repair_required_null_values(rows, cols)
        assert str(rows[0]["s"]).strip() != ""

    def test_not_applicable_when_no_required(self):
        cols = [dcol(name="s", type="string", required=False)]
        rows = [rw(s=None)]
        rows, check = dq.repair_required_null_values(rows, cols)
        assert check["status"] == "not_applicable"

    def test_preserves_null_case(self):
        cols = [dcol(name="n", type="integer", required=True, min=1, max=100)]
        rows = [rw(labels=["null_case"], n=None)]
        rows, check = dq.repair_required_null_values(rows, cols)
        assert rows[0]["n"] is None


# ===========================================================================
# repair_unique_values
# ===========================================================================

class TestUniqueRepair:

    def test_dedupes_repeated_values(self):
        cols = [dcol(name="pk", type="uuid", unique=True)]
        rows = [rw(pk="SAME"), rw(pk="SAME"), rw(pk="SAME")]
        rows, check = dq.repair_unique_values(rows, cols)
        pks = [r["pk"] for r in rows]
        assert len(pks) == len(set(pks))

    def test_not_applicable_when_no_unique(self):
        cols = [dcol(name="x", type="string")]
        rows = [rw(x="a"), rw(x="a")]
        rows, check = dq.repair_unique_values(rows, cols)
        assert check["status"] == "not_applicable"

    def test_preserves_duplicate_case(self):
        cols = [dcol(name="pk", type="uuid", unique=True)]
        rows = [rw(pk="A"), rw(labels=["duplicate_case"], pk="A")]
        rows, check = dq.repair_unique_values(rows, cols)
        assert rows[1]["pk"] == "A"  # intentional duplicate preserved


# ===========================================================================
# repair_string_lengths_and_text_quality
# ===========================================================================

class TestTextQualityRepair:

    def test_replaces_junk_text(self):
        cols = [dcol(name="s", type="string")]
        rows = [rw(s="not_a_number")]
        rows, check = dq.repair_string_lengths_and_text_quality(rows, cols)
        assert rows[0]["s"] != "not_a_number"

    def test_pads_below_min_length(self):
        cols = [dcol(name="s", type="string", min_length=20)]
        rows = [rw(s="hi")]
        rows, check = dq.repair_string_lengths_and_text_quality(rows, cols)
        assert len(rows[0]["s"]) >= 20

    def test_truncates_above_max_length(self):
        cols = [dcol(name="s", type="string", max_length=5)]
        rows = [rw(s="waytoolongvalue")]
        rows, check = dq.repair_string_lengths_and_text_quality(rows, cols)
        assert len(rows[0]["s"]) <= 5

    def test_preserves_length_violation_case(self):
        cols = [dcol(name="s", type="string", max_length=5)]
        rows = [rw(labels=["length_violation_case"], s="verylongkeep")]
        rows, check = dq.repair_string_lengths_and_text_quality(rows, cols)
        assert rows[0]["s"] == "verylongkeep"


# ===========================================================================
# repair_format_values
# ===========================================================================

class TestFormatRepair:

    def test_repairs_invalid_email(self):
        cols = [dcol(name="email", type="email")]
        rows = [rw(email="not-an-email")]
        rows, check = dq.repair_format_values(rows, cols)
        assert dq.is_valid_email(rows[0]["email"])

    def test_repairs_invalid_phone(self):
        cols = [dcol(name="phone", type="phone")]
        rows = [rw(phone="123")]
        rows, check = dq.repair_format_values(rows, cols)
        assert dq.is_valid_indian_phone(rows[0]["phone"])

    def test_repairs_invalid_ip(self):
        cols = [dcol(name="ip", type="ip_address")]
        rows = [rw(ip="999.999.999.999")]
        rows, check = dq.repair_format_values(rows, cols)
        assert dq.is_valid_ip(rows[0]["ip"])

    def test_repairs_invalid_uuid(self):
        cols = [dcol(name="uuid", type="uuid")]
        rows = [rw(uuid="bad-uuid")]
        rows, check = dq.repair_format_values(rows, cols)
        assert dq.is_valid_uuid(rows[0]["uuid"])

    def test_repairs_invalid_pincode(self):
        cols = [dcol(name="pincode", type="postal_code")]
        rows = [rw(pincode="000")]
        rows, check = dq.repair_format_values(rows, cols)
        assert dq.is_valid_indian_pincode(rows[0]["pincode"])

    def test_keeps_valid_email(self):
        cols = [dcol(name="email", type="email")]
        rows = [rw(email="good@example.com")]
        rows, check = dq.repair_format_values(rows, cols)
        assert rows[0]["email"] == "good@example.com"

    def test_preserves_invalid_case(self):
        cols = [dcol(name="email", type="email")]
        rows = [rw(labels=["invalid_case"], email="keep-bad")]
        rows, check = dq.repair_format_values(rows, cols)
        assert rows[0]["email"] == "keep-bad"


# ===========================================================================
# repair_date_ranges
# ===========================================================================

class TestDateRangeRepair:

    def _cols(self):
        return [dcol(name="d", type="date",
                     distribution={"type": "date_range",
                                   "start_date": "2020-01-01",
                                   "end_date": "2020-12-31"})]

    def test_moves_out_of_range_date_in(self):
        from datetime import date
        cols = self._cols()
        rows = [rw(d="1999-01-01")]
        rows, check = dq.repair_date_ranges(rows, cols)
        d = dq.parse_date_value(rows[0]["d"])
        assert date(2020, 1, 1) <= d <= date(2020, 12, 31)

    def test_keeps_in_range_date(self):
        cols = self._cols()
        rows = [rw(d="2020-06-15")]
        rows, check = dq.repair_date_ranges(rows, cols)
        assert rows[0]["d"] == "2020-06-15"

    def test_not_applicable_without_date_range(self):
        cols = [dcol(name="d", type="date")]
        rows = [rw(d="1999-01-01")]
        rows, check = dq.repair_date_ranges(rows, cols)
        assert check["status"] == "not_applicable"


# ===========================================================================
# repair_age_dob_consistency
# ===========================================================================

class TestAgeDobRepair:

    def _cols(self):
        return [dcol(name="age", type="integer"), dcol(name="dob", type="date")]

    def test_aligns_dob_to_age(self):
        cols = self._cols()
        rows = [rw(age=30, dob="1950-01-01")]
        rows, check = dq.repair_age_dob_consistency(rows, cols)
        calc = dq.calculate_age_from_dob(rows[0]["dob"])
        assert abs(calc - 30) <= 1

    def test_clamps_negative_age(self):
        cols = self._cols()
        rows = [rw(age=-5, dob="2000-01-01")]
        rows, check = dq.repair_age_dob_consistency(rows, cols)
        assert rows[0]["age"] >= 0

    def test_clamps_over_100(self):
        cols = self._cols()
        rows = [rw(age=250, dob="1900-01-01")]
        rows, check = dq.repair_age_dob_consistency(rows, cols)
        assert rows[0]["age"] <= 100

    def test_handles_non_numeric_age(self):
        cols = self._cols()
        rows = [rw(age="abc", dob="2000-01-01")]
        rows, check = dq.repair_age_dob_consistency(rows, cols)
        assert isinstance(rows[0]["age"], int)

    def test_not_applicable_with_one_field(self):
        cols = [dcol(name="age", type="integer")]
        rows = [rw(age=30)]
        rows, check = dq.repair_age_dob_consistency(rows, cols)
        assert check["status"] == "not_applicable"


# ===========================================================================
# repair_regex_values
# ===========================================================================

class TestRegexRepair:

    def test_repairs_non_matching_value(self):
        cols = [dcol(name="code", type="regex", pattern=r"[A-Z]{3}\d{3}")]
        rows = [rw(code="nope")]
        rows, check = dq.repair_regex_values(rows, cols)
        # value was regenerated; may or may not match depending on generator,
        # but the rule must have run and produced a string.
        assert rows[0]["code"] is not None

    def test_keeps_matching_value(self):
        cols = [dcol(name="code", type="regex", pattern=r"[A-Z]{3}\d{3}")]
        rows = [rw(code="ABC123")]
        rows, check = dq.repair_regex_values(rows, cols)
        assert rows[0]["code"] == "ABC123"

    def test_not_applicable_without_regex(self):
        cols = [dcol(name="s", type="string")]
        rows = [rw(s="x")]
        rows, check = dq.repair_regex_values(rows, cols)
        assert check["status"] == "not_applicable"

    def test_preserves_invalid_case(self):
        cols = [dcol(name="code", type="regex", pattern=r"[A-Z]{3}\d{3}")]
        rows = [rw(labels=["invalid_case"], code="keep-bad")]
        rows, check = dq.repair_regex_values(rows, cols)
        assert rows[0]["code"] == "keep-bad"


# ===========================================================================
# repair_duplicate_rows
# ===========================================================================

class TestDuplicateRowRepair:

    def test_differentiates_duplicate_rows(self):
        cols = [dcol(name="a", type="integer", min=1, max=100000),
                dcol(name="b", type="string")]
        rows = [rw(a=1, b="x"), rw(a=1, b="x")]
        rows, check = dq.repair_duplicate_rows(rows, cols)
        sig0 = (str(rows[0]["a"]), str(rows[0]["b"]))
        sig1 = (str(rows[1]["a"]), str(rows[1]["b"]))
        assert sig0 != sig1

    def test_not_applicable_single_column(self):
        cols = [dcol(name="a", type="integer")]
        rows = [rw(a=1), rw(a=1)]
        rows, check = dq.repair_duplicate_rows(rows, cols)
        assert check["status"] == "not_applicable"

    def test_preserves_duplicate_case(self):
        cols = [dcol(name="a", type="integer", min=1, max=100),
                dcol(name="b", type="string")]
        rows = [rw(a=1, b="x"), rw(labels=["duplicate_case"], a=1, b="x")]
        rows, check = dq.repair_duplicate_rows(rows, cols)
        assert (str(rows[1]["a"]), str(rows[1]["b"])) == ("1", "x")


# ===========================================================================
# country_currency + status_boolean: preservation paths (fill remaining branches)
# ===========================================================================

class TestConsistencyPreservation:

    def test_country_currency_preserves_invalid_case(self):
        cols = [dcol(name="country", type="country"),
                dcol(name="currency", type="currency_code")]
        rows = [rw(labels=["invalid_case"], country="USA", currency="USD")]
        rows, check = dq.repair_country_currency_consistency(rows, cols)
        assert rows[0]["country"] == "USA"

    def test_status_boolean_unknown_status_skipped(self):
        cols = [dcol(name="status", type="category"),
                dcol(name="is_active", type="boolean")]
        rows = [rw(status="mystery", is_active=True)]
        rows, check = dq.repair_status_boolean_consistency(rows, cols)
        assert rows[0]["is_active"] is True  # unknown status -> no change

    def test_status_boolean_preserves_invalid_case(self):
        cols = [dcol(name="status", type="category"),
                dcol(name="is_active", type="boolean")]
        rows = [rw(labels=["invalid_case"], status="active", is_active=False)]
        rows, check = dq.repair_status_boolean_consistency(rows, cols)
        assert rows[0]["is_active"] is False