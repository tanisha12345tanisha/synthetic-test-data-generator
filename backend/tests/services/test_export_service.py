"""
Strict adversarial unit tests for app/services/export_service.py

Exports must be lossless and safe:
  1. Filename safety: spaces collapsed, empty/whitespace names get a default,
     extension correct per format.
  2. JSON export: parses back to the exact original rows (full round-trip).
  3. CSV/PSV export: metadata list/dict columns are JSON-serialized; data
     round-trips via the same delimiter; embedded delimiters/quotes/newlines
     are correctly escaped (this is the classic injection risk).
  4. Streaming contract: correct media_type and Content-Disposition.
"""

import asyncio
import io
import json

import pandas as pd
import pytest

from app.services import export_service as ex


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_stream(response):
    """Concatenate a StreamingResponse body into a single string.

    Starlette wraps body_iterator as an ASYNC generator, so we drain it with
    asyncio. Also handles the plain sync iterator (iter([...])) used by the
    CSV/PSV exporters."""
    async def _drain():
        chunks = []
        iterator = response.body_iterator
        if hasattr(iterator, "__aiter__"):
            async for chunk in iterator:
                chunks.append(chunk)
        else:
            for chunk in iterator:
                chunks.append(chunk)
        return chunks

    raw_chunks = asyncio.run(_drain())
    decoded = []
    for chunk in raw_chunks:
        if isinstance(chunk, bytes):
            chunk = chunk.decode("utf-8")
        decoded.append(chunk)
    return "".join(decoded)


def make_result(rows, dataset_name="my dataset"):
    return {
        "dataset_name": dataset_name,
        "row_count": len(rows),
        "generated_rows": rows,
    }


def simple_rows():
    return [
        {"id": 1, "name": "Alice",
         "__case_type": "normal", "__case_labels": ["normal"], "__case_reasons": []},
        {"id": 2, "name": "Bob",
         "__case_type": "edge_case", "__case_labels": ["edge_case"], "__case_reasons": []},
    ]


# ===========================================================================
# safe_file_name
# ===========================================================================

class TestSafeFileName:

    def test_spaces_become_underscores(self):
        assert ex.safe_file_name("my data set", "csv") == "my_data_set.csv"

    def test_trims_whitespace(self):
        assert ex.safe_file_name("  report  ", "json") == "report.json"

    def test_empty_name_default(self):
        assert ex.safe_file_name("", "csv") == "synthetic_dataset.csv"

    def test_whitespace_only_name_default(self):
        assert ex.safe_file_name("   ", "psv") == "synthetic_dataset.psv"

    @pytest.mark.parametrize("ext", ["csv", "json", "psv"])
    def test_extension_applied(self, ext):
        assert ex.safe_file_name("data", ext).endswith(f".{ext}")


# ===========================================================================
# JSON export
# ===========================================================================

class TestJsonExport:

    def test_media_type_and_filename(self):
        resp = ex.export_dataset_as_json(make_result(simple_rows(), "sales data"))
        assert resp.media_type == "application/json"
        assert "sales_data.json" in resp.headers["content-disposition"]

    def test_round_trips_exactly(self):
        rows = simple_rows()
        resp = ex.export_dataset_as_json(make_result(rows))
        parsed = json.loads(read_stream(resp))
        assert parsed == rows  # full fidelity, metadata preserved as native lists

    def test_unicode_preserved(self):
        rows = [{"city": "बेंगलुरु", "__case_type": "normal",
                 "__case_labels": ["normal"], "__case_reasons": []}]
        resp = ex.export_dataset_as_json(make_result(rows))
        body = read_stream(resp)
        assert "बेंगलुरु" in body  # ensure_ascii=False keeps it readable
        assert json.loads(body) == rows


# ===========================================================================
# CSV export
# ===========================================================================

class TestCsvExport:

    def test_media_type_and_filename(self):
        resp = ex.export_dataset_as_csv(make_result(simple_rows(), "q1 report"))
        assert resp.media_type == "text/csv"
        assert "q1_report.csv" in resp.headers["content-disposition"]

    def test_header_and_row_count(self):
        resp = ex.export_dataset_as_csv(make_result(simple_rows()))
        df = pd.read_csv(io.StringIO(read_stream(resp)))
        assert len(df) == 2
        assert set(["id", "name", "__case_type", "__case_labels", "__case_reasons"]).issubset(df.columns)

    def test_metadata_columns_are_json_strings(self):
        resp = ex.export_dataset_as_csv(make_result(simple_rows()))
        df = pd.read_csv(io.StringIO(read_stream(resp)))
        # __case_labels serialized as JSON -> parseable back to a list
        first = json.loads(df.iloc[0]["__case_labels"])
        assert first == ["normal"]

    def test_embedded_comma_is_escaped_and_round_trips(self):
        rows = [{"id": 1, "note": "hello, world",
                 "__case_type": "normal", "__case_labels": ["normal"], "__case_reasons": []}]
        resp = ex.export_dataset_as_csv(make_result(rows))
        df = pd.read_csv(io.StringIO(read_stream(resp)))
        assert df.iloc[0]["note"] == "hello, world"  # comma must not split the field

    def test_embedded_quote_and_newline_round_trip(self):
        rows = [{"id": 1, "note": 'she said "hi"\nnew line',
                 "__case_type": "normal", "__case_labels": ["normal"], "__case_reasons": []}]
        resp = ex.export_dataset_as_csv(make_result(rows))
        df = pd.read_csv(io.StringIO(read_stream(resp)))
        assert df.iloc[0]["note"] == 'she said "hi"\nnew line'


# ===========================================================================
# PSV (pipe) export
# ===========================================================================

class TestPipeExport:

    def test_media_type_and_filename(self):
        resp = ex.export_dataset_as_pipe(make_result(simple_rows(), "pipe out"))
        assert resp.media_type == "text/plain"
        assert "pipe_out.psv" in resp.headers["content-disposition"]

    def test_pipe_delimited_round_trip(self):
        resp = ex.export_dataset_as_pipe(make_result(simple_rows()))
        df = pd.read_csv(io.StringIO(read_stream(resp)), sep="|")
        assert len(df) == 2
        assert df.iloc[0]["name"] == "Alice"

    def test_embedded_pipe_is_escaped_and_round_trips(self):
        """The whole point of PSV: a value containing '|' must not break the
        column structure. It should be quoted/escaped and round-trip cleanly."""
        rows = [{"id": 1, "note": "a|b|c",
                 "__case_type": "normal", "__case_labels": ["normal"], "__case_reasons": []}]
        resp = ex.export_dataset_as_pipe(make_result(rows))
        df = pd.read_csv(io.StringIO(read_stream(resp)), sep="|")
        assert len(df) == 1
        assert df.iloc[0]["note"] == "a|b|c"


# ===========================================================================
# SUSPECTED BUGS -- expected to (possibly) FAIL. Do NOT weaken.
# ===========================================================================

class TestSuspectedBugs:

    def test_bug_filename_header_injection_via_newline(self):
        """HTTP header safety. safe_file_name only replaces spaces; it does not
        strip CR/LF or other control chars. A dataset_name containing a newline
        injects into the Content-Disposition header, enabling header splitting.
        Expectation: the resulting header value must not contain a raw newline."""
        resp = ex.export_dataset_as_csv(make_result(simple_rows(), "evil\nSet-Cookie: x=1"))
        disposition = resp.headers["content-disposition"]
        assert "\n" not in disposition and "\r" not in disposition, (
            "newline/CR leaked into Content-Disposition header"
        )

    def test_bug_ragged_rows_do_not_create_phantom_columns(self):
        """Schema stability. If rows have differing keys (e.g. an optional field
        missing on some rows), pandas.DataFrame fills the gaps with NaN. This
        checks the union column is present for the row that HAS it and blank
        (not garbage) for the row that lacks it."""
        rows = [
            {"id": 1, "extra": "present",
             "__case_type": "normal", "__case_labels": ["normal"], "__case_reasons": []},
            {"id": 2,
             "__case_type": "normal", "__case_labels": ["normal"], "__case_reasons": []},
        ]
        resp = ex.export_dataset_as_csv(make_result(rows))
        df = pd.read_csv(io.StringIO(read_stream(resp)))
        # Row 0 keeps its value; row 1's missing 'extra' must be empty, not wrong.
        assert df.iloc[0]["extra"] == "present"
        assert pd.isna(df.iloc[1]["extra"])