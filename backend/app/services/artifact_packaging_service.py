import csv
from io import BytesIO, StringIO
import json
import zipfile
from typing import Any


def json_bytes(document: Any) -> bytes:
    return json.dumps(document, ensure_ascii=False, indent=2, default=str).encode("utf-8")


def csv_bytes(rows: list[dict[str, Any]], delimiter: str = ",") -> bytes:
    buffer=StringIO(newline="")
    fields=list(rows[0]) if rows else []
    writer=csv.DictWriter(buffer, fieldnames=fields, delimiter=delimiter)
    writer.writeheader(); writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def connected_zip_bytes(tables: dict[str, list[dict[str, Any]]], schema: dict[str, Any], relationship_report: dict[str, Any], quality_report: dict[str, Any]) -> bytes:
    output=BytesIO()
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as archive:
        for name,rows in sorted(tables.items()): archive.writestr(f"tables/{name}.csv",csv_bytes(rows))
        archive.writestr("schema_snapshot.json",json_bytes(schema))
        archive.writestr("relationship_manifest.json",json_bytes(schema.get("relationships",[])))
        archive.writestr("relationship_report.json",json_bytes(relationship_report))
        archive.writestr("quality_report.json",json_bytes(quality_report))
    return output.getvalue()
