"""
Strict unit tests for app/reference_data/india_locations.py

The reference table is the backbone of city -> pincode -> street consistency in
the generator. A single wrong pincode or duplicated locality silently corrupts
every "consistent address" we produce. These tests validate the data *hard*.
"""

import re

import pytest

from app.reference_data.india_locations import INDIA_LOCATION_REFERENCE


REQUIRED_KEYS = {"country", "state", "city", "locality", "pincode", "streets"}

# India PIN first digit -> allowed states (postal region correctness).
# Ref: India Post postal-region numbering.
STATE_TO_PIN_FIRST_DIGIT = {
    "Delhi": {"1"},
    "Rajasthan": {"3"},
    "Gujarat": {"3"},
    "Maharashtra": {"4"},
    "Madhya Pradesh": {"4"},
    "Goa": {"4"},
    "Karnataka": {"5"},
    "Telangana": {"5"},
    "Andhra Pradesh": {"5"},
    "Tamil Nadu": {"6"},
    "Kerala": {"6"},
    "West Bengal": {"7"},
    "Odisha": {"7"},
}


# ---------------------------------------------------------------------------
# Top-level shape
# ---------------------------------------------------------------------------

def test_reference_is_non_empty_list():
    assert isinstance(INDIA_LOCATION_REFERENCE, list)
    assert len(INDIA_LOCATION_REFERENCE) > 0


@pytest.mark.parametrize("entry", INDIA_LOCATION_REFERENCE)
def test_entry_is_dict_with_exact_keys(entry):
    assert isinstance(entry, dict)
    assert set(entry.keys()) == REQUIRED_KEYS, (
        f"Entry keys {set(entry.keys())} != required {REQUIRED_KEYS}"
    )


# ---------------------------------------------------------------------------
# Field-level correctness
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("entry", INDIA_LOCATION_REFERENCE)
def test_country_is_india(entry):
    assert entry["country"] == "India"


@pytest.mark.parametrize("entry", INDIA_LOCATION_REFERENCE)
def test_text_fields_non_empty_and_clean(entry):
    for field in ["state", "city", "locality"]:
        val = entry[field]
        assert isinstance(val, str), f"{field} not str in {entry['locality']}"
        assert val.strip() != "", f"Empty {field} in {entry}"
        assert val == val.strip(), f"Whitespace padding in {field}: {val!r}"


@pytest.mark.parametrize("entry", INDIA_LOCATION_REFERENCE)
def test_pincode_is_valid_indian_format(entry):
    pin = entry["pincode"]
    assert isinstance(pin, str), f"pincode must be str, got {type(pin)}"
    assert re.fullmatch(r"\d{6}", pin), f"pincode not 6 digits: {pin!r}"
    # Indian PIN codes never start with 0.
    assert pin[0] != "0", f"Indian PIN cannot start with 0: {pin!r}"


@pytest.mark.parametrize("entry", INDIA_LOCATION_REFERENCE)
def test_pincode_region_matches_state(entry):
    """Strongest data-correctness check: the PIN's first digit must belong to
    the postal region of its state. Catches transposed / wrong pincodes."""
    state = entry["state"]
    pin_first = entry["pincode"][0]
    allowed = STATE_TO_PIN_FIRST_DIGIT.get(state)
    assert allowed is not None, f"Unmapped state (extend the map): {state!r}"
    assert pin_first in allowed, (
        f"{entry['locality']} ({state}) has PIN {entry['pincode']} whose region "
        f"digit {pin_first} is not valid for {state} (expected {allowed})"
    )


# ---------------------------------------------------------------------------
# Streets integrity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("entry", INDIA_LOCATION_REFERENCE)
def test_streets_non_empty_unique_clean(entry):
    streets = entry["streets"]
    assert isinstance(streets, list), "streets must be a list"
    assert len(streets) >= 1, f"No streets for {entry['locality']}"
    for s in streets:
        assert isinstance(s, str), f"Street not str: {s!r}"
        assert s.strip() != "", f"Empty street in {entry['locality']}"
        assert s == s.strip(), f"Whitespace padding in street: {s!r}"
    assert len(streets) == len(set(streets)), (
        f"Duplicate street within {entry['locality']}: {streets}"
    )


# ---------------------------------------------------------------------------
# Cross-entry integrity
# ---------------------------------------------------------------------------

def test_localities_are_globally_unique():
    localities = [e["locality"] for e in INDIA_LOCATION_REFERENCE]
    dupes = {l for l in localities if localities.count(l) > 1}
    assert not dupes, f"Duplicate localities: {dupes}"


def test_pincodes_are_globally_unique():
    pins = [e["pincode"] for e in INDIA_LOCATION_REFERENCE]
    dupes = {p for p in pins if pins.count(p) > 1}
    assert not dupes, f"Duplicate pincodes across localities: {dupes}"


def test_city_maps_to_single_state():
    """A city name must not appear under two different states."""
    seen = {}
    for e in INDIA_LOCATION_REFERENCE:
        city, state = e["city"], e["state"]
        if city in seen:
            assert seen[city] == state, (
                f"City {city!r} mapped to both {seen[city]!r} and {state!r}"
            )
        else:
            seen[city] = state


def test_every_state_covered_by_pin_map():
    """Guard: if a new state is added to the data, the region map must be
    extended too, otherwise the correctness check above is silently skipped."""
    states = {e["state"] for e in INDIA_LOCATION_REFERENCE}
    missing = states - set(STATE_TO_PIN_FIRST_DIGIT.keys())
    assert not missing, f"States missing from PIN-region map: {missing}"