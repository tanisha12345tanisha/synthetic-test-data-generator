"""
Strict adversarial unit tests for app/models/schema_models.py

Structure:
  - TestDistributionConfig
  - TestCaseDistributionConfig
  - TestColumnSchema
  - TestDatasetRequest
  - TestPlainModels          (CaseReason/QualityCheck/QualityReport/DatasetSummary/DatasetResponse)
  - TestSuspectedBugs        <-- these are EXPECTED TO FAIL against current source.
                                 Each failure is a real bug to fix in the SOURCE, not the test.

Note on exceptions: Pydantic v2 wraps ValueError raised inside a `model_validator`
into `ValidationError`, so every "should reject" case is asserted with
`pytest.raises(ValidationError)`.
"""

import pytest
from pydantic import ValidationError

from app.models.schema_models import (
    DistributionConfig,
    CaseDistributionConfig,
    ColumnSchema,
    DatasetRequest,
    CaseReason,
    QualityCheck,
    QualityReport,
    DatasetSummary,
    DatasetResponse,
)


# ===========================================================================
# DistributionConfig
# ===========================================================================

class TestDistributionConfig:

    def test_defaults_are_uniform_and_valid(self):
        d = DistributionConfig()
        assert d.type == "uniform"
        assert d.min is None and d.max is None

    def test_type_is_case_insensitive_normal(self):
        # "NORMAL" should normalize and be accepted with a positive std.
        d = DistributionConfig(type="NORMAL", std=2.0)
        assert d.type == "NORMAL"          # original preserved
        assert d.std == 2.0

    @pytest.mark.parametrize("dtype", [
        "uniform", "normal", "exponential",
        "weighted", "boolean_probability", "date_range",
    ])
    def test_all_supported_types_constructible(self, dtype):
        kwargs = {"type": dtype}
        if dtype == "weighted":
            kwargs["weights"] = {"a": 1.0, "b": 2.0}
        if dtype == "date_range":
            kwargs["start_date"] = "2020-01-01"
            kwargs["end_date"] = "2020-12-31"
        d = DistributionConfig(**kwargs)
        assert d.type == dtype

    def test_unsupported_type_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(type="gaussian_ish")

    def test_min_greater_than_max_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(type="uniform", min=10.0, max=1.0)

    def test_min_equal_max_allowed(self):
        d = DistributionConfig(type="uniform", min=5.0, max=5.0)
        assert d.min == d.max == 5.0

    def test_normal_std_zero_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(type="normal", std=0)

    def test_normal_std_negative_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(type="normal", std=-1.0)

    def test_weighted_requires_weights(self):
        with pytest.raises(ValidationError):
            DistributionConfig(type="weighted")

    def test_weighted_empty_weights_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(type="weighted", weights={})

    def test_weighted_zero_sum_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(type="weighted", weights={"a": 0.0, "b": 0.0})

    def test_weighted_positive_sum_ok(self):
        d = DistributionConfig(type="weighted", weights={"a": 1.0, "b": 3.0})
        assert sum(d.weights.values()) == 4.0

    def test_true_probability_bounds(self):
        # Field constraint ge=0, le=100.
        assert DistributionConfig(true_probability=0).true_probability == 0
        assert DistributionConfig(true_probability=100).true_probability == 100

    def test_true_probability_above_100_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(true_probability=100.01)

    def test_true_probability_negative_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(true_probability=-0.5)

    def test_date_range_requires_both_dates(self):
        with pytest.raises(ValidationError):
            DistributionConfig(type="date_range", start_date="2020-01-01")
        with pytest.raises(ValidationError):
            DistributionConfig(type="date_range", end_date="2020-01-01")

    def test_date_range_valid(self):
        d = DistributionConfig(
            type="date_range", start_date="2020-01-01", end_date="2020-12-31"
        )
        assert d.start_date == "2020-01-01"

    def test_date_range_same_day_allowed(self):
        d = DistributionConfig(
            type="date_range", start_date="2020-06-15", end_date="2020-06-15"
        )
        assert d.start_date == d.end_date

    def test_date_range_start_after_end_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(
                type="date_range", start_date="2020-12-31", end_date="2020-01-01"
            )

    def test_date_range_impossible_calendar_date_rejected(self):
        # Feb 30 does not exist -> strptime fails -> format error.
        with pytest.raises(ValidationError):
            DistributionConfig(
                type="date_range", start_date="2020-02-30", end_date="2020-12-31"
            )

    def test_date_range_bad_format_rejected(self):
        with pytest.raises(ValidationError):
            DistributionConfig(
                type="date_range", start_date="31-12-2020", end_date="2020-12-31"
            )


# ===========================================================================
# CaseDistributionConfig
# ===========================================================================

class TestCaseDistributionConfig:

    def test_defaults_sum_to_100(self):
        c = CaseDistributionConfig()
        total = (
            c.normal + c.edge_case + c.corner_case + c.boundary_case
            + c.invalid_case + c.duplicate_case + c.null_case
            + c.format_violation_case + c.range_violation_case
            + c.length_violation_case
        )
        assert total == 100

    def test_custom_valid_distribution(self):
        c = CaseDistributionConfig(
            normal=100, edge_case=0, corner_case=0, boundary_case=0,
            invalid_case=0, duplicate_case=0, null_case=0,
            format_violation_case=0, range_violation_case=0,
            length_violation_case=0,
        )
        assert c.normal == 100

    def test_total_not_100_rejected(self):
        with pytest.raises(ValidationError):
            CaseDistributionConfig(normal=50)  # others default -> total 80

    def test_total_over_100_rejected(self):
        with pytest.raises(ValidationError):
            CaseDistributionConfig(normal=100, edge_case=100)

    def test_negative_field_rejected(self):
        with pytest.raises(ValidationError):
            CaseDistributionConfig(normal=-1)

    def test_field_above_100_rejected(self):
        with pytest.raises(ValidationError):
            CaseDistributionConfig(normal=101)


# ===========================================================================
# ColumnSchema
# ===========================================================================

class TestColumnSchema:

    def test_minimal_valid_column(self):
        col = ColumnSchema(name="age", type="integer")
        assert col.name == "age"
        assert col.required is True
        assert col.nullable is False
        assert col.unique is False

    def test_type_is_case_insensitive(self):
        col = ColumnSchema(name="c", type="STRING")
        assert col.type == "STRING"  # original preserved, validation passed

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="   ", type="string")

    def test_reserved_metadata_name_rejected(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="__case_type", type="string")

    def test_reserved_metadata_name_with_spaces_rejected(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="  __case_labels  ", type="string")

    def test_unsupported_type_rejected(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="c", type="matrix")

    def test_min_greater_than_max_rejected(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="c", type="integer", min=10, max=5)

    def test_min_equal_max_allowed(self):
        col = ColumnSchema(name="c", type="integer", min=5, max=5)
        assert col.min == col.max

    def test_min_length_greater_than_max_length_rejected(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="c", type="string", min_length=10, max_length=2)

    def test_category_requires_values(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="c", type="category")

    def test_category_empty_values_rejected(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="c", type="category", values=[])

    def test_category_with_values_ok(self):
        col = ColumnSchema(name="c", type="category", values=["a", "b"])
        assert col.values == ["a", "b"]

    def test_id_requires_prefix(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="c", type="id")

    def test_id_with_prefix_ok(self):
        col = ColumnSchema(name="c", type="id", prefix="CUST_")
        assert col.prefix == "CUST_"

    def test_regex_requires_pattern(self):
        with pytest.raises(ValidationError):
            ColumnSchema(name="c", type="regex")

    def test_regex_with_pattern_ok(self):
        col = ColumnSchema(name="c", type="regex", pattern=r"\d{3}")
        assert col.pattern == r"\d{3}"

    def test_category_weighted_missing_weight_rejected(self):
        # value "b" has no weight -> must raise.
        with pytest.raises(ValidationError):
            ColumnSchema(
                name="c",
                type="category",
                values=["a", "b"],
                distribution=DistributionConfig(type="weighted", weights={"a": 1.0}),
            )

    def test_category_weighted_all_weights_present_ok(self):
        col = ColumnSchema(
            name="c",
            type="category",
            values=["a", "b"],
            distribution=DistributionConfig(
                type="weighted", weights={"a": 1.0, "b": 2.0}
            ),
        )
        assert col.distribution.type == "weighted"


# ===========================================================================
# DatasetRequest
# ===========================================================================

def _valid_column():
    return ColumnSchema(name="id", type="integer")


class TestDatasetRequest:

    def test_minimal_valid_request(self):
        req = DatasetRequest(
            dataset_name="demo", row_count=10, columns=[_valid_column()]
        )
        assert req.row_count == 10
        # default case_distribution injected and valid
        assert isinstance(req.case_distribution, CaseDistributionConfig)

    def test_empty_dataset_name_rejected(self):
        with pytest.raises(ValidationError):
            DatasetRequest(dataset_name="   ", row_count=10, columns=[_valid_column()])

    def test_row_count_zero_rejected(self):
        with pytest.raises(ValidationError):
            DatasetRequest(dataset_name="d", row_count=0, columns=[_valid_column()])

    def test_row_count_above_max_rejected(self):
        with pytest.raises(ValidationError):
            DatasetRequest(dataset_name="d", row_count=10001, columns=[_valid_column()])

    def test_row_count_boundaries_ok(self):
        assert DatasetRequest(
            dataset_name="d", row_count=1, columns=[_valid_column()]
        ).row_count == 1
        assert DatasetRequest(
            dataset_name="d", row_count=10000, columns=[_valid_column()]
        ).row_count == 10000

    def test_no_columns_rejected(self):
        with pytest.raises(ValidationError):
            DatasetRequest(dataset_name="d", row_count=10, columns=[])

    def test_duplicate_column_names_case_insensitive_rejected(self):
        with pytest.raises(ValidationError):
            DatasetRequest(
                dataset_name="d",
                row_count=10,
                columns=[
                    ColumnSchema(name="Name", type="string"),
                    ColumnSchema(name="name", type="string"),
                ],
            )

    def test_default_case_distribution_is_valid(self):
        req = DatasetRequest(
            dataset_name="d", row_count=5, columns=[_valid_column()]
        )
        assert req.case_distribution.normal == 70


# ===========================================================================
# Plain models (structural)
# ===========================================================================

def _summary_kwargs():
    return dict(
        dataset_name="d",
        total_rows=10,
        total_columns=3,
        seed=None,
        synthetic_only=True,
        preview_recommended_rows=5,
        normal_rows=7,
        edge_case_rows=1,
        corner_case_rows=0,
        boundary_case_rows=0,
        invalid_case_rows=1,
        duplicate_case_rows=0,
        null_case_rows=1,
        format_violation_case_rows=0,
        range_violation_case_rows=0,
        length_violation_case_rows=0,
    )


class TestPlainModels:

    def test_case_reason(self):
        r = CaseReason(column="c", label="null_case", reason="x")
        assert r.column == "c"

    def test_case_reason_missing_field_rejected(self):
        with pytest.raises(ValidationError):
            CaseReason(column="c", label="null_case")

    def test_quality_check_defaults(self):
        q = QualityCheck(rule="pincode", status="passed")
        assert q.rows_checked == 0
        assert q.rows_repaired == 0
        assert q.failed_rows == 0
        assert q.fields_detected is None

    def test_quality_report(self):
        qr = QualityReport(
            overall_score=99.5,
            rules_checked=4,
            rules_passed=4,
            rules_failed=0,
            checks=[{"rule": "x", "status": "passed"}],
        )
        assert qr.overall_score == 99.5

    def test_dataset_summary_requires_seed_field(self):
        # seed is Optional[int] with NO default -> field is required (accepts None).
        kwargs = _summary_kwargs()
        del kwargs["seed"]
        with pytest.raises(ValidationError):
            DatasetSummary(**kwargs)

    def test_dataset_summary_valid(self):
        s = DatasetSummary(**_summary_kwargs())
        assert s.synthetic_only is True
        assert s.data_quality_score is None

    def test_dataset_response_valid(self):
        resp = DatasetResponse(
            dataset_name="d",
            row_count=1,
            generated_rows=[{"id": 1}],
            summary=DatasetSummary(**_summary_kwargs()),
        )
        assert resp.quality_report is None
        assert resp.row_count == 1


# ===========================================================================
# SUSPECTED BUGS  --  these SHOULD pass if the code is correct.
# I expect them to FAIL against the current source. Each failure = 1 bug.
# DO NOT weaken these tests; fix the source.
# ===========================================================================

class TestSuspectedBugs:

    def test_bug_negative_min_length_should_be_rejected(self):
        """min_length has no ge=0 constraint. A negative length is nonsensical
        for a string field and should be rejected, but the model accepts it."""
        with pytest.raises(ValidationError):
            ColumnSchema(name="c", type="string", min_length=-5)

    def test_bug_negative_max_length_should_be_rejected(self):
        """max_length has no ge=0 constraint; negative max length is invalid."""
        with pytest.raises(ValidationError):
            ColumnSchema(name="c", type="string", max_length=-1)

    def test_bug_weighted_negative_weight_should_be_rejected(self):
        """Weighted distribution only checks that the SUM > 0. Individual
        negative weights (which are meaningless for sampling) slip through as
        long as the total stays positive."""
        with pytest.raises(ValidationError):
            DistributionConfig(type="weighted", weights={"a": -1.0, "b": 5.0})

    def test_bug_date_not_zero_padded_should_be_rejected(self):
        """The error message promises 'YYYY-MM-DD', but strptime('%Y-%m-%d')
        also accepts non-zero-padded values like '2020-1-1', contradicting the
        stated contract."""
        with pytest.raises(ValidationError):
            DistributionConfig(
                type="date_range", start_date="2020-1-1", end_date="2020-12-31"
            )

    def test_bug_two_digit_year_should_be_rejected(self):
        """strptime('%Y-%m-%d') happily parses a 2-digit year ('99-01-01' -> year 99),
        which is not a valid YYYY date."""
        with pytest.raises(ValidationError):
            DistributionConfig(
                type="date_range", start_date="99-01-01", end_date="2020-12-31"
            )