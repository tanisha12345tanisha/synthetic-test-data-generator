"""
Strict unit tests for app/utils/constants.py

These tests encode the INTENDED contract of the constants module and act as
regression guards. They intentionally assert invariants that a careless future
edit could break (typos, whitespace, wrong types, accidental deletions).
"""

import pytest

from app.utils import constants


# ---------------------------------------------------------------------------
# Existence & type contract
# ---------------------------------------------------------------------------

def test_all_expected_symbols_exist():
    for name in [
        "SUPPORTED_DATA_TYPES",
        "SUPPORTED_DISTRIBUTIONS",
        "CASE_LABELS",
        "METADATA_COLUMNS",
        "SYNTHETIC_ONLY_POLICY",
    ]:
        assert hasattr(constants, name), f"Missing constant: {name}"


@pytest.mark.parametrize("obj_name", [
    "SUPPORTED_DATA_TYPES",
    "SUPPORTED_DISTRIBUTIONS",
    "CASE_LABELS",
    "METADATA_COLUMNS",
])
def test_collections_are_sets(obj_name):
    assert isinstance(getattr(constants, obj_name), set)


def test_policy_is_dict():
    assert isinstance(constants.SYNTHETIC_ONLY_POLICY, dict)


# ---------------------------------------------------------------------------
# Non-empty & member cleanliness
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("s", [
    constants.SUPPORTED_DATA_TYPES,
    constants.SUPPORTED_DISTRIBUTIONS,
    constants.CASE_LABELS,
    constants.METADATA_COLUMNS,
])
def test_sets_are_non_empty(s):
    assert len(s) > 0


@pytest.mark.parametrize("s", [
    constants.SUPPORTED_DATA_TYPES,
    constants.SUPPORTED_DISTRIBUTIONS,
    constants.CASE_LABELS,
])
def test_members_are_clean_lowercase_tokens(s):
    """Every token must be a non-empty, stripped, lowercase string with no
    internal spaces (identifiers used as keys elsewhere in the pipeline)."""
    for token in s:
        assert isinstance(token, str), f"Non-string member: {token!r}"
        assert token != "", "Empty string member found"
        assert token == token.strip(), f"Whitespace padding in: {token!r}"
        assert token == token.lower(), f"Non-lowercase token: {token!r}"
        assert " " not in token, f"Space inside token: {token!r}"


# ---------------------------------------------------------------------------
# Metadata column invariants
# ---------------------------------------------------------------------------

def test_metadata_columns_double_underscore_prefixed():
    for col in constants.METADATA_COLUMNS:
        assert col.startswith("__"), f"Metadata column not '__'-prefixed: {col!r}"


def test_metadata_columns_do_not_collide_with_data_types():
    """Metadata/internal columns must never overlap with real data types,
    otherwise a generated field could be silently treated as metadata."""
    assert constants.METADATA_COLUMNS.isdisjoint(constants.SUPPORTED_DATA_TYPES)


def test_metadata_columns_do_not_collide_with_case_labels():
    assert constants.METADATA_COLUMNS.isdisjoint(constants.CASE_LABELS)


# ---------------------------------------------------------------------------
# Documented alias / key presence (behavioural expectations)
# ---------------------------------------------------------------------------

def test_postal_aliases_present():
    # Both spellings are supported aliases in the schema layer.
    assert {"postal_code", "zip"}.issubset(constants.SUPPORTED_DATA_TYPES)


def test_identifier_types_present():
    assert {"uuid", "id"}.issubset(constants.SUPPORTED_DATA_TYPES)


def test_name_family_present():
    assert {"name", "first_name", "last_name"}.issubset(constants.SUPPORTED_DATA_TYPES)


def test_core_case_labels_present():
    for required in ["normal", "invalid_case", "null_case", "duplicate_case"]:
        assert required in constants.CASE_LABELS


# ---------------------------------------------------------------------------
# Synthetic-only policy contract
# ---------------------------------------------------------------------------

def test_policy_has_required_keys():
    assert set(["enabled", "message"]).issubset(constants.SYNTHETIC_ONLY_POLICY.keys())


def test_policy_enabled_is_true_bool():
    val = constants.SYNTHETIC_ONLY_POLICY["enabled"]
    assert isinstance(val, bool)
    assert val is True


def test_policy_message_is_meaningful():
    msg = constants.SYNTHETIC_ONLY_POLICY["message"]
    assert isinstance(msg, str)
    assert len(msg.strip()) > 10
    assert "synthetic" in msg.lower()


# ---------------------------------------------------------------------------
# Regression guards (snapshot of expected membership counts)
# ---------------------------------------------------------------------------

def test_expected_counts_snapshot():
    """If someone accidentally deletes or duplicates a member, this fails.
    Update deliberately when the contract genuinely changes."""
    assert len(constants.SUPPORTED_DATA_TYPES) == 31
    assert len(constants.SUPPORTED_DISTRIBUTIONS) == 6
    assert len(constants.CASE_LABELS) == 11
    assert len(constants.METADATA_COLUMNS) == 3