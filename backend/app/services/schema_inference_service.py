import re
import pandas as pd


def infer_id_prefix(series):
    non_null_values = series.dropna().astype(str).tolist()

    if not non_null_values:
        return "ID"

    first_value = non_null_values[0]
    match = re.match(r"^[A-Za-z]+", first_value)

    if match:
        return match.group(0).upper()

    return "ID"


def infer_column_type(series, column_name):
    column_name_lower = column_name.lower()
    non_null_series = series.dropna()

    if non_null_series.empty:
        return "string"

    if "email" in column_name_lower:
        return "email"

    if "phone" in column_name_lower or "mobile" in column_name_lower:
        return "phone"

    if column_name_lower.endswith("_id") or column_name_lower == "id" or "customer_id" in column_name_lower:
        return "id"

    if "date" in column_name_lower or "dob" in column_name_lower:
        return "date"

    if "amount" in column_name_lower or "price" in column_name_lower or "salary" in column_name_lower:
        return "currency_amount"

    if "city" in column_name_lower:
        return "category"

    if "state" in column_name_lower:
        return "category"

    if "country" in column_name_lower:
        return "category"

    if "status" in column_name_lower:
        return "category"

    if "type" in column_name_lower or "category" in column_name_lower:
        return "category"

    if "name" in column_name_lower:
        return "name"

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_integer_dtype(series):
        return "integer"

    if pd.api.types.is_float_dtype(series):
        return "decimal"

    unique_count = non_null_series.nunique()
    total_count = len(non_null_series)

    if total_count > 0:
        unique_ratio = unique_count / total_count

        if unique_count <= 20 and unique_ratio <= 0.8:
            return "category"

    return "string"


def should_mark_unique(series, inferred_type, column_name):
    if inferred_type in ["id", "email", "uuid"]:
        return True

    if inferred_type == "phone":
        return True

    return False


def infer_schema_from_dataframe(df):
    columns = []

    for column_name in df.columns:
        series = df[column_name]
        inferred_type = infer_column_type(series, column_name)

        column_schema = {
            "name": column_name,
            "type": inferred_type,
            "required": bool(series.isna().sum() == 0),
            "nullable": bool(series.isna().sum() > 0),
            "unique": should_mark_unique(series, inferred_type, column_name),
            "min": None,
            "max": None,
            "min_length": None,
            "max_length": None,
            "values": None,
            "prefix": None,
            "pattern": None,
            "distribution": None
        }

        if inferred_type in ["integer", "number", "decimal", "float", "currency_amount"]:
            clean_series = pd.to_numeric(series, errors="coerce").dropna()

            if not clean_series.empty:
                column_schema["min"] = float(clean_series.min())
                column_schema["max"] = float(clean_series.max())
                column_schema["distribution"] = {
                    "type": "uniform",
                    "min": float(clean_series.min()),
                    "max": float(clean_series.max())
                }

        if inferred_type == "date":
            extracted_dates = (
                series
                .astype(str)
                .str.strip()
                .str.extract(r"(\d{4}-\d{2}-\d{2})")[0]
            )

            clean_dates = pd.to_datetime(
                extracted_dates,
                errors="coerce"
            ).dropna()

            if not clean_dates.empty:
                start_date = clean_dates.min().date().isoformat()
                end_date = clean_dates.max().date().isoformat()

                column_schema["distribution"] = {
                    "type": "date_range",
                    "start_date": start_date,
                    "end_date": end_date
                }

        if inferred_type == "category":
            values = series.dropna().astype(str).unique().tolist()
            values = values[:50]

            column_schema["values"] = values
            column_schema["distribution"] = {
                "type": "weighted",
                "weights": {
                    str(value): int((series.astype(str) == str(value)).sum())
                    for value in values
                }
            }

        if inferred_type == "id":
            column_schema["prefix"] = infer_id_prefix(series)

        columns.append(column_schema)

    return {
        "synthetic_only": True,
        "message": "CSV was used only for schema inference. Uploaded values are not copied into generated output.",
        "row_count_detected": len(df),
        "columns_detected": len(df.columns),
        "columns": columns
    }


def infer_schema_from_csv(file):
    try:
        df = pd.read_csv(file.file)
    except pd.errors.EmptyDataError:
        raise ValueError("Uploaded CSV is empty.")
    except Exception:
        raise ValueError("Unable to read uploaded CSV file.")

    if df.empty:
        raise ValueError("Uploaded CSV does not contain any data rows.")

    if len(df.columns) == 0:
        raise ValueError("Uploaded CSV does not contain any columns.")

    return infer_schema_from_dataframe(df)