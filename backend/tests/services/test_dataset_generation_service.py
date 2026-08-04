"""
Strict adversarial unit tests for app/services/dataset_generation_service.py

This is the ORCHESTRATOR. It wires together case selection, normal generation,
case-value generation, unique tracking, data-quality repair, and summary math.
Correctness here means:
  1. Row-count integrity: exactly row_count rows; every row carries the 3
     metadata columns plus all declared data columns.
  2. Metadata integrity: __case_type is a known type; __case_labels are all valid
     CASE_LABELS; __case_reasons is a list; normal rows have empty reasons.
  3. Uniqueness: unique columns with adequate value space stay unique.
  4. Determinism: same seed -> identical dataset (uuid excluded, see Segment 3).
  5. Summary math: per-case counters reflect the labels actually emitted.

Pure-unit tests target build_final_case_labels / calculate_case_counts directly.
Integration tests exercise generate_normal_dataset end to end (this transitively
calls data_quality_service, so it runs in your env, not my sandbox).

TestSuspectedBugs are HYPOTHESES expected to FAIL against current source. Do NOT
weaken them; fix the source or record a signed-off design decision.
"""

import random

import pytest

from app.models.schema_models import (
    ColumnSchema, DatasetRequest, CaseDistributionConfig,
)
from app.utils.constants import CASE_LABELS
from app.services import dataset_generation_service as ds


CONFIG_CASE_TYPES = [
    "normal", "edge_case", "corner_case", "boundary_case", "invalid_case",
    "duplicate_case", "null_case", "format_violation_case",
    "range_violation_case", "length_violation_case",
]

METADATA_KEYS = {"__case_type", "__case_labels", "__case_reasons"}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def col(**kwargs):
    base = {"name": "c", "type": "string"}
    base.update(kwargs)
    return ColumnSchema(**base)


def all_normal_distribution():
    return CaseDistributionConfig(
        normal=100, edge_case=0, corner_case=0, boundary_case=0,
        invalid_case=0, duplicate_case=0, null_case=0,
        format_violation_case=0, range_violation_case=0,
        length_violation_case=0,
    )


def single_case_distribution(case_field):
    fields = {ct: 0 for ct in CONFIG_CASE_TYPES}
    fields[case_field] = 100
    return CaseDistributionConfig(**fields)


def make_request(columns, row_count=50, seed=123, case_distribution=None):
    return DatasetRequest(
        dataset_name="demo",
        row_count=row_count,
        seed=seed,
        columns=columns,
        case_distribution=case_distribution or all_normal_distribution(),
    )


# ===========================================================================
# Pure unit: build_final_case_labels
# ===========================================================================

class TestBuildFinalCaseLabels:

    def test_no_reasons_returns_base_copy(self):
        base = ["normal"]
        out = ds.build_final_case_labels(base, [])
        assert out == ["normal"]
        assert out is not base  # must be a copy, not the same list

    def test_reason_label_appended_when_missing(self):
        out = ds.build_final_case_labels(["boundary_case"], [{"label": "boundary_case"}])
        assert out == ["boundary_case"]  # already present, not duplicated

    def test_new_reason_label_added(self):
        out = ds.build_final_case_labels(["corner_case"], [{"label": "null_case"}])
        assert out == ["corner_case", "null_case"]

    def test_all_labels_remain_valid(self):
        out = ds.build_final_case_labels(
            ["range_violation_case", "invalid_case"],
            [{"label": "range_violation_case"}],
        )
        for label in out:
            assert label in CASE_LABELS


# ===========================================================================
# Pure unit: calculate_case_counts
# ===========================================================================

class TestCalculateCaseCounts:

    def test_counts_by_primary_case_type(self):
        rows = [
            {"__case_type": "normal", "__case_labels": ["normal"]},
            {"__case_type": "normal", "__case_labels": ["normal"]},
            {"__case_type": "edge_case", "__case_labels": ["edge_case"]},
        ]
        counts = ds.calculate_case_counts(rows)
        assert counts["normal"] == 2
        assert counts["edge_case"] == 1

    def test_violation_row_counted_once_not_double(self):
        # range_violation row carries both labels but must count ONCE.
        rows = [{
            "__case_type": "range_violation_case",
            "__case_labels": ["range_violation_case", "invalid_case"],
        }]
        counts = ds.calculate_case_counts(rows)
        assert counts["range_violation_case"] == 1
        assert counts["invalid_case"] == 0  # no double count
        assert sum(counts.values()) == 1

    def test_unknown_case_type_ignored(self):
        rows = [{"__case_type": "mixed_case"}, {"__case_type": "totally_new"}]
        counts = ds.calculate_case_counts(rows)
        assert all(v == 0 for v in counts.values())

    def test_missing_case_type_is_safe(self):
        counts = ds.calculate_case_counts([{}])
        assert all(v == 0 for v in counts.values())


# ===========================================================================
# Integration: basic contract
# ===========================================================================

class TestBasicContract:

    def test_row_count_matches(self):
        req = make_request([col(name="a", type="integer", min=1, max=100)], row_count=37)
        out = ds.generate_normal_dataset(req)
        assert len(out["generated_rows"]) == 37
        assert out["row_count"] == 37

    def test_every_row_has_all_columns_and_metadata(self):
        cols = [
            col(name="a", type="integer", min=1, max=100),
            col(name="b", type="email"),
        ]
        req = make_request(cols, row_count=25)
        out = ds.generate_normal_dataset(req)
        for row in out["generated_rows"]:
            assert "a" in row and "b" in row
            assert METADATA_KEYS.issubset(row.keys())

    def test_case_type_is_known(self):
        req = make_request([col(name="a", type="integer", min=1, max=100)],
                           row_count=50, case_distribution=CaseDistributionConfig())
        out = ds.generate_normal_dataset(req)
        for row in out["generated_rows"]:
            assert row["__case_type"] in CONFIG_CASE_TYPES

    def test_all_case_labels_valid(self):
        req = make_request([col(name="a", type="integer", min=1, max=100),
                            col(name="b", type="string", min_length=2, max_length=10)],
                           row_count=80, case_distribution=CaseDistributionConfig())
        out = ds.generate_normal_dataset(req)
        for row in out["generated_rows"]:
            assert isinstance(row["__case_labels"], list)
            for label in row["__case_labels"]:
                assert label in CASE_LABELS
            assert isinstance(row["__case_reasons"], list)

    def test_summary_structure(self):
        req = make_request([col(name="a", type="integer", min=1, max=100)], row_count=30)
        out = ds.generate_normal_dataset(req)
        summary = out["summary"]
        assert summary["total_rows"] == 30
        assert summary["total_columns"] == 1
        assert summary["synthetic_only"] is True
        assert "data_quality_score" in summary


# ===========================================================================
# Integration: all-normal
# ===========================================================================

class TestAllNormal:

    def test_all_rows_normal(self):
        req = make_request([col(name="a", type="integer", min=1, max=100)],
                           row_count=40, case_distribution=all_normal_distribution())
        out = ds.generate_normal_dataset(req)
        for row in out["generated_rows"]:
            assert row["__case_type"] == "normal"
            assert row["__case_labels"] == ["normal"]
            assert row["__case_reasons"] == []

    def test_summary_case_rows_partition_total(self):
        """After Option A fix: the 10 per-case counters partition total_rows
        exactly -- each row counted once by its primary __case_type. Violation
        rows are NOT double-counted under invalid_case."""
        req = make_request(
            [col(name="n", type="integer", min=1, max=10)],
            row_count=50,
            case_distribution=single_case_distribution("range_violation_case"),
        )
        out = ds.generate_normal_dataset(req)
        s = out["summary"]
        per_case_total = (
            s["normal_rows"] + s["edge_case_rows"] + s["corner_case_rows"]
            + s["boundary_case_rows"] + s["invalid_case_rows"]
            + s["duplicate_case_rows"] + s["null_case_rows"]
            + s["format_violation_case_rows"] + s["range_violation_case_rows"]
            + s["length_violation_case_rows"]
        )
        assert per_case_total == s["total_rows"]
        assert s["range_violation_case_rows"] == 50
        assert s["invalid_case_rows"] == 0

    def test_row_count_one_boundary(self):
        req = make_request([col(name="a", type="integer", min=1, max=100)],
                           row_count=1, case_distribution=all_normal_distribution())
        out = ds.generate_normal_dataset(req)
        assert len(out["generated_rows"]) == 1


# ===========================================================================
# Integration: determinism (uuid excluded)
# ===========================================================================

class TestDeterminism:

    def _cols(self):
        return [
            col(name="pk", type="id", prefix="C_"),
            col(name="n", type="integer", min=1, max=1000),
            col(name="mail", type="email"),
            col(name="cat", type="category", values=["x", "y", "z"]),
            col(name="fn", type="first_name"),
        ]

    def test_same_seed_identical_dataset(self):
        req1 = make_request(self._cols(), row_count=60, seed=777,
                            case_distribution=CaseDistributionConfig())
        req2 = make_request(self._cols(), row_count=60, seed=777,
                            case_distribution=CaseDistributionConfig())
        out1 = ds.generate_normal_dataset(req1)
        out2 = ds.generate_normal_dataset(req2)
        assert out1["generated_rows"] == out2["generated_rows"]


# ===========================================================================
# Integration: uniqueness
# ===========================================================================

class TestUniqueness:

    def test_unique_id_column_all_unique(self):
        # id type is inherently unique (row_index based); confirm no dupes.
        req = make_request([col(name="pk", type="id", prefix="U_", unique=True)],
                           row_count=200, case_distribution=all_normal_distribution())
        out = ds.generate_normal_dataset(req)
        pks = [r["pk"] for r in out["generated_rows"]]
        assert len(pks) == len(set(pks))

    def test_unique_uuid_column_all_unique(self):
        req = make_request([col(name="pk", type="uuid", unique=True)],
                           row_count=300, case_distribution=all_normal_distribution())
        out = ds.generate_normal_dataset(req)
        pks = [r["pk"] for r in out["generated_rows"]]
        assert len(pks) == len(set(pks))


# ===========================================================================
# SUSPECTED BUGS -- expected to FAIL. Do NOT weaken.
# ===========================================================================

class TestSuspectedBugs:

    def test_bug_summary_case_rows_sum_to_total(self):
        """Summary double-counting. Violation rows carry TWO labels, e.g.
        ['range_violation_case', 'invalid_case']. calculate_case_counts then
        increments BOTH counters, so invalid_case_rows overlaps with the
        specific violation counters and the 10 per-case row counts sum to MORE
        than total_rows. If the summary is meant to partition rows (each row
        counted once), this is a bug; if invalid_case_rows is intentionally an
        umbrella superset, this is a documented design choice."""
        req = make_request(
            [col(name="n", type="integer", min=1, max=10)],
            row_count=50,
            case_distribution=single_case_distribution("range_violation_case"),
        )
        out = ds.generate_normal_dataset(req)
        s = out["summary"]
        per_case_total = (
            s["normal_rows"] + s["edge_case_rows"] + s["corner_case_rows"]
            + s["boundary_case_rows"] + s["invalid_case_rows"]
            + s["duplicate_case_rows"] + s["null_case_rows"]
            + s["format_violation_case_rows"] + s["range_violation_case_rows"]
            + s["length_violation_case_rows"]
        )
        assert per_case_total == s["total_rows"], (
            f"per-case counts sum to {per_case_total} but total_rows is "
            f"{s['total_rows']} (invalid_case double-counts violation rows)"
        )

    def test_bug_unique_over_constrained_column_keeps_type(self):
        """Type contamination in the unique-collision fallback. When a unique
        column's value space is too small (e.g. unique integer in [1,5] with 20
        rows), generate_unique_value exhausts its retries and falls back to
        f'{value}_{row_index+1}_{attempts}', injecting STRING values like
        '3_11_100' into what should be an integer column. The column ends up
        mixing ints and strings, breaking downstream typing."""
        req = make_request(
            [col(name="n", type="integer", min=1, max=5, unique=True)],
            row_count=20,
            case_distribution=all_normal_distribution(),
        )
        out = ds.generate_normal_dataset(req)
        types = {type(r["n"]).__name__ for r in out["generated_rows"]}
        assert types == {"int"}, (
            f"unique integer column contains mixed types: {sorted(types)}"
        )
