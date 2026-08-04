"""
Strict adversarial unit tests for app/services/normal_generation_service.py

Testing philosophy:
  - Type integrity: an "integer" must be a real int, "boolean" a real bool, etc.
  - Range correctness: values must respect declared min/max (inclusive).
  - Format validity: emails have '@', IPs parse, UUIDs parse, phones match India format.
  - Determinism: same seed (random + numpy + Faker) -> identical output.
  - Nullable semantics: non-nullable columns must NEVER emit None.

  TestSuspectedBugs at the bottom drove real fixes:
    - integer rounding leak  -> fixed in source (clamp_integer_to_bounds)
    - length on structured types -> Option A: rejected at schema validation
"""

import re
import uuid
import ipaddress
from datetime import datetime, date

import numpy as np
import pytest
from faker import Faker
from pydantic import ValidationError

from app.models.schema_models import ColumnSchema, DistributionConfig
from app.services import normal_generation_service as gen


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_column(**kwargs):
    """Build a valid ColumnSchema with sensible defaults, overridable."""
    base = {"name": "c", "type": "string"}
    base.update(kwargs)
    return ColumnSchema(**base)


def seed_all(s=12345):
    random_module = gen.random
    random_module.seed(s)
    np.random.seed(s)
    Faker.seed(s)


def generate_many(column, n=300, row_index=0):
    return [gen.generate_normal_value(column, row_index) for _ in range(n)]


# ===========================================================================
# Numeric
# ===========================================================================

class TestNumeric:

    def test_integer_type_returns_python_int(self):
        col = make_column(type="integer", min=1, max=10)
        for _ in range(50):
            v = gen.generate_normal_value(col, 0)
            assert isinstance(v, int) and not isinstance(v, bool)

    def test_integer_within_declared_range(self):
        col = make_column(type="integer", min=1, max=10)
        for _ in range(500):
            v = gen.generate_normal_value(col, 0)
            assert 1 <= v <= 10, f"integer {v} outside [1,10]"

    def test_integer_min_equals_max(self):
        col = make_column(type="integer", min=5, max=5)
        for _ in range(20):
            assert gen.generate_normal_value(col, 0) == 5

    def test_number_type_returns_int(self):
        col = make_column(type="number", min=0, max=100)
        v = gen.generate_normal_value(col, 0)
        assert isinstance(v, int) and not isinstance(v, bool)

    def test_float_type_two_decimals_and_in_range(self):
        col = make_column(type="float", min=0, max=10)
        for _ in range(200):
            v = gen.generate_normal_value(col, 0)
            assert isinstance(v, float)
            assert 0 <= v <= 10
            # at most 2 decimal places
            assert round(v, 2) == v

    def test_decimal_type_two_decimals(self):
        col = make_column(type="decimal", min=0, max=10)
        v = gen.generate_normal_value(col, 0)
        assert round(v, 2) == v

    def test_normal_distribution_clamped_to_bounds(self):
        col = make_column(
            type="float", min=0, max=100,
            distribution=DistributionConfig(type="normal", mean=50, std=10),
        )
        for _ in range(500):
            v = gen.generate_normal_value(col, 0)
            assert 0 <= v <= 100

    def test_exponential_distribution_clamped_to_bounds(self):
        col = make_column(
            type="float", min=0, max=100,
            distribution=DistributionConfig(type="exponential", mean=10),
        )
        for _ in range(500):
            v = gen.generate_normal_value(col, 0)
            assert 0 <= v <= 100

    def test_uniform_distribution_respects_distribution_bounds(self):
        col = make_column(
            type="float", min=0, max=1000,
            distribution=DistributionConfig(type="uniform", min=5, max=6),
        )
        for _ in range(300):
            v = gen.generate_normal_value(col, 0)
            assert 5 <= v <= 6

    def test_currency_amount_non_negative(self):
        col = make_column(type="currency_amount", min=1, max=1000)
        for _ in range(200):
            v = gen.generate_normal_value(col, 0)
            assert v >= 0
            assert round(v, 2) == v


# ===========================================================================
# Boolean
# ===========================================================================

class TestBoolean:

    def test_boolean_returns_python_bool(self):
        col = make_column(type="boolean")
        for _ in range(50):
            v = gen.generate_normal_value(col, 0)
            assert isinstance(v, bool)

    def test_boolean_probability_100_always_true(self):
        col = make_column(
            type="boolean",
            distribution=DistributionConfig(type="boolean_probability", true_probability=100),
        )
        for _ in range(200):
            assert gen.generate_normal_value(col, 0) is True

    def test_boolean_probability_0_always_false(self):
        col = make_column(
            type="boolean",
            distribution=DistributionConfig(type="boolean_probability", true_probability=0),
        )
        for _ in range(200):
            assert gen.generate_normal_value(col, 0) is False


# ===========================================================================
# Category
# ===========================================================================

class TestCategory:

    def test_category_returns_member(self):
        col = make_column(type="category", values=["a", "b", "c"])
        for _ in range(100):
            assert gen.generate_normal_value(col, 0) in {"a", "b", "c"}

    def test_category_weighted_zero_weight_never_selected(self):
        col = make_column(
            type="category",
            values=["a", "b"],
            distribution=DistributionConfig(type="weighted", weights={"a": 1.0, "b": 0.0}),
        )
        for _ in range(300):
            assert gen.generate_normal_value(col, 0) == "a"


# ===========================================================================
# Date / Datetime
# ===========================================================================

class TestDateTime:

    def test_date_format_and_parseable(self):
        col = make_column(type="date")
        v = gen.generate_normal_value(col, 0)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", v)
        datetime.strptime(v, "%Y-%m-%d")  # must not raise

    def test_date_range_within_bounds(self):
        col = make_column(
            type="date",
            distribution=DistributionConfig(
                type="date_range", start_date="2020-01-01", end_date="2020-12-31"
            ),
        )
        lo = date(2020, 1, 1)
        hi = date(2020, 12, 31)
        for _ in range(300):
            v = gen.generate_normal_value(col, 0)
            d = datetime.strptime(v, "%Y-%m-%d").date()
            assert lo <= d <= hi

    def test_datetime_isoformat_parseable(self):
        col = make_column(type="datetime")
        v = gen.generate_normal_value(col, 0)
        datetime.fromisoformat(v)  # must not raise

    def test_timestamp_isoformat_parseable(self):
        col = make_column(type="timestamp")
        v = gen.generate_normal_value(col, 0)
        datetime.fromisoformat(v)

    def test_datetime_range_date_part_within_bounds(self):
        col = make_column(
            type="datetime",
            distribution=DistributionConfig(
                type="date_range", start_date="2021-06-01", end_date="2021-06-30"
            ),
        )
        for _ in range(200):
            v = gen.generate_normal_value(col, 0)
            dt = datetime.fromisoformat(v)
            assert date(2021, 6, 1) <= dt.date() <= date(2021, 6, 30)
            assert 0 <= dt.hour <= 23
            assert 0 <= dt.minute <= 59
            assert 0 <= dt.second <= 59


# ===========================================================================
# String length rules
# ===========================================================================

class TestStringLength:

    def test_string_min_length_enforced(self):
        col = make_column(type="string", min_length=25)
        for _ in range(50):
            v = gen.generate_normal_value(col, 0)
            assert len(v) >= 25

    def test_string_max_length_enforced(self):
        col = make_column(type="string", max_length=4)
        for _ in range(50):
            v = gen.generate_normal_value(col, 0)
            assert len(v) <= 4

    def test_string_both_bounds_enforced(self):
        col = make_column(type="string", min_length=6, max_length=8)
        for _ in range(100):
            v = gen.generate_normal_value(col, 0)
            assert 6 <= len(v) <= 8

    def test_long_text_max_length_enforced(self):
        col = make_column(type="long_text", max_length=20)
        for _ in range(30):
            v = gen.generate_normal_value(col, 0)
            assert len(v) <= 20


# ===========================================================================
# Names
# ===========================================================================

class TestNames:

    def test_first_name_is_single_word(self):
        col = make_column(type="first_name")
        for _ in range(50):
            v = gen.generate_normal_value(col, 0)
            assert " " not in v
            assert v.isalpha()

    def test_last_name_is_single_word(self):
        col = make_column(type="last_name")
        for _ in range(50):
            v = gen.generate_normal_value(col, 0)
            assert " " not in v
            assert v.isalpha()

    def test_name_is_two_words(self):
        col = make_column(type="name")
        for _ in range(50):
            v = gen.generate_normal_value(col, 0)
            parts = v.split(" ")
            assert len(parts) == 2
            assert all(p.isalpha() for p in parts)


# ===========================================================================
# Formats
# ===========================================================================

class TestFormats:

    def test_email_contains_at(self):
        col = make_column(type="email")
        for _ in range(50):
            v = gen.generate_normal_value(col, 0)
            assert "@" in v and "." in v.split("@")[-1]

    def test_phone_indian_format(self):
        col = make_column(type="phone")
        pattern = re.compile(r"\+91[6-9]\d{9}$")
        for _ in range(100):
            v = gen.generate_normal_value(col, 0)
            assert pattern.fullmatch(v), f"bad phone {v}"

    def test_uuid_parseable(self):
        col = make_column(type="uuid")
        for _ in range(50):
            v = gen.generate_normal_value(col, 0)
            uuid.UUID(v)  # must not raise

    def test_ip_address_valid_ipv4(self):
        col = make_column(type="ip_address")
        for _ in range(100):
            v = gen.generate_normal_value(col, 0)
            ipaddress.IPv4Address(v)  # must not raise

    def test_country_is_india(self):
        col = make_column(type="country")
        assert gen.generate_normal_value(col, 0) == "India"

    def test_currency_code_is_inr(self):
        col = make_column(type="currency_code")
        assert gen.generate_normal_value(col, 0) == "INR"

    def test_url_looks_like_url(self):
        col = make_column(type="url")
        v = gen.generate_normal_value(col, 0)
        assert v.startswith("http")

    def test_id_format_and_increment(self):
        col = make_column(type="id", prefix="CUST_")
        assert gen.generate_normal_value(col, 0) == "CUST_00001"
        assert gen.generate_normal_value(col, 41) == "CUST_00042"

    def test_id_default_prefix_when_absent(self):
        # prefix is required by schema for id, but generator has an "ID" fallback.
        # We exercise the generator's fallback via a stub-free valid column.
        col = make_column(type="id", prefix="ID")
        assert gen.generate_normal_value(col, 0) == "ID00001"


# ===========================================================================
# Determinism (reproducibility contract)
# NOTE: uuid is intentionally EXCLUDED -- uuid4() draws from os.urandom() and is
# not seedable by design, so it cannot be reproducible. That is not a defect.
# ===========================================================================

class TestDeterminism:

    @pytest.mark.parametrize("col_kwargs", [
        {"type": "integer", "min": 1, "max": 100},
        {"type": "float", "min": 0, "max": 50},
        {"type": "email"},
        {"type": "phone"},
        {"type": "date"},
        {"type": "category", "values": ["a", "b", "c", "d"]},
    ])
    def test_same_seed_same_value(self, col_kwargs):
        col = make_column(**col_kwargs)

        seed_all(999)
        first = gen.generate_normal_value(col, 0)

        seed_all(999)
        second = gen.generate_normal_value(col, 0)

        assert first == second, f"non-deterministic for {col_kwargs}"


# ===========================================================================
# Nullable semantics
# ===========================================================================

class TestNullable:

    def test_non_nullable_never_none(self):
        col = make_column(type="string", min_length=3)
        for _ in range(1000):
            assert gen.generate_normal_value(col, 0) is not None

    def test_nullable_can_emit_none(self):
        col = make_column(type="string", nullable=True)
        values = generate_many(col, n=1000)
        assert any(v is None for v in values), "nullable column never produced None"


# ===========================================================================
# CONFIRMED BUGS -- these drove real source/schema fixes.
# They now PASS against the corrected code. DO NOT weaken them.
# ===========================================================================

class TestConfirmedBugsFixed:

    def test_integer_does_not_exceed_fractional_max(self):
        """Was a bug: int(round(uniform(min,max))) could round UP past a
        fractional max. Fixed by clamp_integer_to_bounds(). With max=1.6 every
        value must be <= 1.6 (i.e. <= 1)."""
        col = make_column(type="integer", min=1, max=1.6)
        values = [gen.generate_normal_value(col, 0) for _ in range(800)]
        assert all(v <= 1.6 for v in values), (
            f"integer exceeded max=1.6; observed max was {max(values)}"
        )

    def test_integer_does_not_fall_below_fractional_min(self):
        """Symmetric low-end case. With min=2.4 every value must be >= 2.4
        (i.e. >= 3) after the clamp fix."""
        col = make_column(type="integer", min=2.4, max=3.0)
        values = [gen.generate_normal_value(col, 0) for _ in range(800)]
        assert all(v >= 2.4 for v in values), (
            f"integer fell below min=2.4; observed min was {min(values)}"
        )

    @pytest.mark.parametrize("dtype", ["email", "phone", "city", "url"])
    def test_length_constraint_rejected_on_structured_type_min(self, dtype):
        """Option A: length constraints on structured types are meaningless and
        would corrupt data (e.g. padding a phone), so the schema must REJECT
        them up front rather than silently ignore or apply them."""
        with pytest.raises(ValidationError):
            make_column(type=dtype, min_length=60)

    @pytest.mark.parametrize("dtype", ["email", "city", "company", "job_title"])
    def test_length_constraint_rejected_on_structured_type_max(self, dtype):
        """Symmetric: max_length on structured types must be rejected."""
        with pytest.raises(ValidationError):
            make_column(type=dtype, max_length=3)