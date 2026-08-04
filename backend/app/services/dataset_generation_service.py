import random
import numpy as np
from faker import Faker

from app.services.normal_generation_service import generate_normal_value
from app.services.case_selection_service import select_case_type, get_case_labels
from app.services.case_value_generation_service import generate_case_value
from app.services.data_quality_service import apply_data_quality_rules


fake = Faker("en_IN")


def build_final_case_labels(base_labels, case_reasons):
    final_labels = list(base_labels)

    for reason in case_reasons:
        reason_label = reason.get("label")

        if reason_label and reason_label not in final_labels:
            final_labels.append(reason_label)

        if reason_label != "normal" and reason_label != "edge_case":
            if "invalid_case" in reason_label and "invalid_case" not in final_labels:
                final_labels.append("invalid_case")

    return final_labels


def initialize_seed(seed):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        Faker.seed(seed)
        fake.seed_instance(seed)


def initialize_unique_trackers(columns):
    unique_trackers = {}

    for column in columns:
        if column.unique:
            unique_trackers[column.name] = set()

    return unique_trackers


def generate_unique_value(column, row_index, unique_trackers):
    value = generate_normal_value(column, row_index)

    if not column.unique:
        return value

    existing_values = unique_trackers[column.name]
    attempts = 0
    max_attempts = 100

    while value in existing_values and attempts < max_attempts:
        value = generate_normal_value(column, row_index + attempts + 1)
        attempts += 1

    if value in existing_values:
        value = f"{value}_{row_index + 1}_{attempts}"

    existing_values.add(value)

    return value


def _columns_of_types(columns, allowed_types):
    return [
        column
        for column in columns
        if column.type.lower() in allowed_types
    ]


def _pick_duplicate_target(columns, unique_trackers):
    columns_with_existing_values = [
        column
        for column in columns
        if column.unique
        and column.name in unique_trackers
        and len(unique_trackers[column.name]) > 0
    ]

    if columns_with_existing_values:
        return random.choice(columns_with_existing_values)

    unique_columns = [column for column in columns if column.unique]

    if unique_columns:
        return random.choice(unique_columns)

    return None


def pick_target_column(columns, case_type, unique_trackers):
    numeric_types = {"integer", "number", "decimal", "float", "currency_amount"}
    text_types = {
        "string", "long_text", "name", "first_name",
        "last_name", "address", "company", "job_title"
    }
    format_sensitive_types = {
        "email", "phone", "uuid", "url", "ip_address",
        "date", "datetime", "timestamp", "boolean"
    }

    case_type_to_allowed_types = {
        "range_violation_case": numeric_types,
        "length_violation_case": text_types,
        "format_violation_case": format_sensitive_types,
        "boundary_case": numeric_types | text_types | {"date", "datetime", "timestamp", "category"},
        "corner_case": numeric_types | text_types | {"date", "datetime", "timestamp", "category", "boolean"},
    }

    if case_type == "duplicate_case":
        duplicate_target = _pick_duplicate_target(columns, unique_trackers)
        if duplicate_target is not None:
            return duplicate_target

    allowed_types = case_type_to_allowed_types.get(case_type)

    if allowed_types:
        candidate_columns = _columns_of_types(columns, allowed_types)
        if candidate_columns:
            return random.choice(candidate_columns)

    return random.choice(columns)


def calculate_case_counts(rows):
    case_counts = {
        "normal": 0,
        "edge_case": 0,
        "corner_case": 0,
        "boundary_case": 0,
        "invalid_case": 0,
        "duplicate_case": 0,
        "null_case": 0,
        "format_violation_case": 0,
        "range_violation_case": 0,
        "length_violation_case": 0
    }

    for row in rows:
        case_type = row.get("__case_type")

        if case_type in case_counts:
            case_counts[case_type] += 1

    return case_counts

def build_row_values(request, case_type, target_column, row_index, unique_trackers):
    row = {}
    case_reasons = []

    for column in request.columns:
        is_case_target = (
            case_type != "normal"
            and target_column is not None
            and column.name == target_column.name
        )

        if is_case_target:
            value, reason = generate_case_value(
                column,
                case_type,
                row_index,
                unique_trackers
            )

            if reason:
                case_reasons.append(reason)

            row[column.name] = value

            if column.unique and case_type != "duplicate_case":
                unique_trackers[column.name].add(value)
        else:
            value = generate_unique_value(
                column,
                row_index,
                unique_trackers
            )
            row[column.name] = value

    return row, case_reasons

def generate_normal_dataset(request):
    initialize_seed(request.seed)

    rows = []
    unique_trackers = initialize_unique_trackers(request.columns)

    for row_index in range(request.row_count):
        case_type = select_case_type(request.case_distribution)
        case_labels = get_case_labels(case_type)

        target_column = None

        if case_type != "normal":
            target_column = pick_target_column(
                request.columns,
                case_type,
                unique_trackers
            )

        row, case_reasons = build_row_values(
            request,
            case_type,
            target_column,
            row_index,
            unique_trackers
        )

        final_case_labels = build_final_case_labels(case_labels, case_reasons)

        row["__case_type"] = case_type
        row["__case_labels"] = final_case_labels
        row["__case_reasons"] = case_reasons

        rows.append(row)

    rows, quality_report = apply_data_quality_rules(
        rows=rows,
        columns=request.columns
    )

    case_counts = calculate_case_counts(rows)

    summary = {
        "dataset_name": request.dataset_name,
        "total_rows": len(rows),
        "total_columns": len(request.columns),
        "seed": request.seed,
        "synthetic_only": True,
        "preview_recommended_rows": 100,

        "normal_rows": case_counts["normal"],
        "edge_case_rows": case_counts["edge_case"],
        "corner_case_rows": case_counts["corner_case"],
        "boundary_case_rows": case_counts["boundary_case"],
        "invalid_case_rows": case_counts["invalid_case"],
        "duplicate_case_rows": case_counts["duplicate_case"],
        "null_case_rows": case_counts["null_case"],
        "format_violation_case_rows": case_counts["format_violation_case"],
        "range_violation_case_rows": case_counts["range_violation_case"],
        "length_violation_case_rows": case_counts["length_violation_case"],

        "data_quality_score": quality_report["overall_score"],
        "data_quality_rules_checked": quality_report["rules_checked"],
        "data_quality_rules_passed": quality_report["rules_passed"],
        "data_quality_rules_failed": quality_report["rules_failed"]
    }

    return {
        "dataset_name": request.dataset_name,
        "row_count": request.row_count,
        "generated_rows": rows,
        "summary": summary,
        "quality_report": quality_report
    }