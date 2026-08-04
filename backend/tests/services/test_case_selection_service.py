"""
Strict adversarial unit tests for app/services/case_selection_service.py

This module is a WEIGHTED RANDOM SELECTOR (not a fixed-quota allocator):
  - build_case_pool: expands a CaseDistributionConfig into a flat pool where each
    case_type appears `percentage` times (pool length == sum of percentages == 100).
  - select_case_type: random.choice over that pool.
  - get_case_labels: maps a case_type to its metadata labels (violation types
    carry the extra "invalid_case" label).

So correctness means:
  1. Pool construction: exact multiplicities, zero-percentage types absent,
     total length == 100 for a valid config.
  2. Proportions: over many draws, observed frequency ~ declared percentage.
  3. Label integrity: every case_type maps to labels that (a) start with itself
     for the 10 config fields, and (b) are all members of CASE_LABELS.

TestSuspectedBugs at the bottom are HYPOTHESES / design questions expected to FAIL
against the current source. Do NOT weaken them; fix the source or sign off on the
design decision.
"""

import random

import pytest

from app.models.schema_models import CaseDistributionConfig
from app.utils.constants import CASE_LABELS
from app.services import case_selection_service as cs


# The 10 case-type fields that make up a CaseDistributionConfig.
CONFIG_CASE_TYPES = [
    "normal", "edge_case", "corner_case", "boundary_case", "invalid_case",
    "duplicate_case", "null_case", "format_violation_case",
    "range_violation_case", "length_violation_case",
]


class _StubDist:
    """Minimal stand-in exposing model_dump(), to exercise edge configs
    (e.g. an all-zero pool) that the real validated model cannot represent."""
    def __init__(self, mapping):
        self._mapping = dict(mapping)

    def model_dump(self):
        return dict(self._mapping)


# ===========================================================================
# build_case_pool
# ===========================================================================

class TestBuildCasePool:

    def test_default_pool_length_is_100(self):
        pool = cs.build_case_pool(CaseDistributionConfig())
        assert len(pool) == 100

    def test_default_pool_exact_multiplicities(self):
        pool = cs.build_case_pool(CaseDistributionConfig())
        expected = {
            "normal": 70, "edge_case": 10, "corner_case": 5, "boundary_case": 5,
            "invalid_case": 5, "duplicate_case": 1, "null_case": 1,
            "format_violation_case": 1, "range_violation_case": 1,
            "length_violation_case": 1,
        }
        for case_type, count in expected.items():
            assert pool.count(case_type) == count, f"{case_type}: {pool.count(case_type)} != {count}"

    def test_zero_percentage_type_absent(self):
        # normal=100, everything else 0 -> only "normal" in pool.
        cfg = CaseDistributionConfig(
            normal=100, edge_case=0, corner_case=0, boundary_case=0,
            invalid_case=0, duplicate_case=0, null_case=0,
            format_violation_case=0, range_violation_case=0,
            length_violation_case=0,
        )
        pool = cs.build_case_pool(cfg)
        assert set(pool) == {"normal"}
        assert len(pool) == 100

    def test_only_config_case_types_present(self):
        pool = cs.build_case_pool(CaseDistributionConfig())
        assert set(pool).issubset(set(CONFIG_CASE_TYPES))

    def test_all_zero_pool_is_empty(self):
        stub = _StubDist({ct: 0 for ct in CONFIG_CASE_TYPES})
        assert cs.build_case_pool(stub) == []


# ===========================================================================
# select_case_type
# ===========================================================================

class TestSelectCaseType:

    def test_returns_a_config_case_type(self):
        cfg = CaseDistributionConfig()
        for _ in range(200):
            assert cs.select_case_type(cfg) in CONFIG_CASE_TYPES

    def test_empty_pool_falls_back_to_normal(self):
        stub = _StubDist({ct: 0 for ct in CONFIG_CASE_TYPES})
        assert cs.select_case_type(stub) == "normal"

    def test_single_type_config_always_returns_it(self):
        cfg = CaseDistributionConfig(
            normal=0, edge_case=100, corner_case=0, boundary_case=0,
            invalid_case=0, duplicate_case=0, null_case=0,
            format_violation_case=0, range_violation_case=0,
            length_violation_case=0,
        )
        for _ in range(100):
            assert cs.select_case_type(cfg) == "edge_case"

    def test_proportions_are_approximately_correct(self):
        """Statistical: with normal=70, observed normal frequency over a large
        sample should be near 0.70. Seeded for reproducibility."""
        random.seed(2026)
        cfg = CaseDistributionConfig()
        n = 20000
        counts = {}
        for _ in range(n):
            ct = cs.select_case_type(cfg)
            counts[ct] = counts.get(ct, 0) + 1
        normal_freq = counts.get("normal", 0) / n
        assert 0.66 <= normal_freq <= 0.74, f"normal freq {normal_freq:.3f} not ~0.70"
        edge_freq = counts.get("edge_case", 0) / n
        assert 0.07 <= edge_freq <= 0.13, f"edge freq {edge_freq:.3f} not ~0.10"


# ===========================================================================
# get_case_labels
# ===========================================================================

class TestGetCaseLabels:

    @pytest.mark.parametrize("case_type", CONFIG_CASE_TYPES)
    def test_first_label_is_the_case_type(self, case_type):
        labels = cs.get_case_labels(case_type)
        assert isinstance(labels, list) and len(labels) >= 1
        assert labels[0] == case_type

    @pytest.mark.parametrize("case_type", CONFIG_CASE_TYPES)
    def test_all_labels_are_valid_case_labels(self, case_type):
        for label in cs.get_case_labels(case_type):
            assert label in CASE_LABELS, f"{label} not in CASE_LABELS"

    @pytest.mark.parametrize("case_type", [
        "format_violation_case", "range_violation_case", "length_violation_case",
    ])
    def test_violation_types_also_tagged_invalid(self, case_type):
        labels = cs.get_case_labels(case_type)
        assert labels[0] == case_type
        assert "invalid_case" in labels

    @pytest.mark.parametrize("case_type", [
        "normal", "edge_case", "corner_case", "boundary_case",
        "invalid_case", "duplicate_case", "null_case",
    ])
    def test_non_violation_types_are_single_label(self, case_type):
        assert cs.get_case_labels(case_type) == [case_type]


# ===========================================================================
# SUSPECTED BUGS / design questions -- expected to FAIL against current source.
# ===========================================================================

class TestSuspectedBugs:

    def test_bug_unknown_case_type_is_echoed_not_relabeled(self):
        """Latent mislabeling risk (same family as the Segment 4 label-integrity
        bugs). get_case_labels falls back to a hard-coded ['mixed_case'] for any
        unrecognized case_type. If a new case type is later added to the config
        but not to this mapping, its rows are silently relabeled 'mixed_case'
        instead of carrying their real type. Safer behavior: echo the actual
        case_type. If you prefer the 'mixed_case' catch-all as intentional, this
        is a design decision and we adjust the test."""
        labels = cs.get_case_labels("future_new_case")
        assert labels == ["future_new_case"], (
            f"unknown type relabeled to {labels} instead of being echoed"
        )