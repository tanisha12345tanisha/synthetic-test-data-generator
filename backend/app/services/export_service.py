import io
import json
import pandas as pd
import re

from fastapi.responses import StreamingResponse


def safe_file_name(dataset_name, extension):
    cleaned_name = dataset_name.strip().replace(" ", "_")

    # Strip anything that isn't a safe filename character. This also removes
    # CR/LF and other control characters, preventing HTTP header injection
    # (response splitting) via the Content-Disposition header.
    cleaned_name = re.sub(r"[^A-Za-z0-9._-]", "", cleaned_name)

    if not cleaned_name:
        cleaned_name = "synthetic_dataset"

    return f"{cleaned_name}.{extension}"


def export_dataset_as_json(dataset_result):
    file_name = safe_file_name(dataset_result["dataset_name"], "json")

    rows = dataset_result["generated_rows"]

    json_content = json.dumps(
        rows,
        indent=2,
        ensure_ascii=False
    )

    stream = io.BytesIO(json_content.encode("utf-8"))

    return StreamingResponse(
        stream,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}"
        }
    )


def export_dataset_as_csv(dataset_result):
    file_name = safe_file_name(dataset_result["dataset_name"], "csv")

    rows = dataset_result["generated_rows"]
    csv_ready_rows = []

    for row in rows:
        csv_row = {}

        for key, value in row.items():
            if key in ["__case_labels", "__case_reasons"]:
                csv_row[key] = json.dumps(value, ensure_ascii=False)
            else:
                csv_row[key] = value

        csv_ready_rows.append(csv_row)

    df = pd.DataFrame(csv_ready_rows)

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}"
        }
    )


def export_dataset_as_pipe(dataset_result):
    file_name = safe_file_name(dataset_result["dataset_name"], "psv")

    rows = dataset_result["generated_rows"]
    pipe_ready_rows = []

    for row in rows:
        pipe_row = {}

        for key, value in row.items():
            if key in ["__case_labels", "__case_reasons"]:
                pipe_row[key] = json.dumps(value, ensure_ascii=False)
            else:
                pipe_row[key] = value

        pipe_ready_rows.append(pipe_row)

    df = pd.DataFrame(pipe_ready_rows)

    stream = io.StringIO()
    df.to_csv(stream, index=False, sep="|")
    stream.seek(0)

    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}"
        }
    )