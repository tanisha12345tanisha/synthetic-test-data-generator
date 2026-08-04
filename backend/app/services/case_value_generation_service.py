import random
from datetime import date, timedelta

from app.services.normal_generation_service import generate_normal_value


def build_reason(column, label, reason):
    return {
        "column": column.name,
        "label": label,
        "reason": reason
    }


def generate_null_case_value(column):
    return None, build_reason(
        column,
        "null_case",
        "null_value_injected"
    )


def generate_range_violation_value(column):
    column_type = column.type.lower()

    if column_type not in ["integer", "number", "decimal", "float", "currency_amount"]:
        value, _ = generate_invalid_case_value(column)
        
        return value, build_reason(
        
            column,
            
            "range_violation_case",
            
            "range_not_applicable_used_invalid_value"
            
            )

    if column.max is not None:
        return column.max + 1, build_reason(
            column,
            "range_violation_case",
            "above_maximum_value"
        )

    if column.min is not None:
        return column.min - 1, build_reason(
            column,
            "range_violation_case",
            "below_minimum_value"
        )

    return -999999, build_reason(
        column,
        "range_violation_case",
        "out_of_expected_range"
    )


def generate_length_violation_value(column):
    column_type = column.type.lower()

    text_types = [
        "string",
        "long_text",
        "name",
        "first_name",
        "last_name",
        "address",
        "company",
        "job_title"
    ]

    if column_type not in text_types:
        value, _ = generate_invalid_case_value(column)
        return value, build_reason(
            column,
            "length_violation_case",
            "length_not_applicable_used_invalid_value"
        )

    if column.max_length is not None:
        return "A" * (column.max_length + 10), build_reason(
            column,
            "length_violation_case",
            "above_max_length"
        )

    if column.min_length is not None:
        return "", build_reason(
            column,
            "length_violation_case",
            "below_min_length"
        )

    return "A" * 500, build_reason(
        column,
        "length_violation_case",
        "very_long_text"
    )


def generate_format_violation_value(column):
    column_type = column.type.lower()

    if column_type == "email":
        return "invalid-email", build_reason(
            column,
            "format_violation_case",
            "invalid_email_format"
        )

    if column_type == "phone":
        return "abc-phone-123", build_reason(
            column,
            "format_violation_case",
            "invalid_phone_format"
        )

    if column_type == "uuid":
        return "invalid-uuid", build_reason(
            column,
            "format_violation_case",
            "invalid_uuid_format"
        )

    if column_type == "url":
        return "not-a-url", build_reason(
            column,
            "format_violation_case",
            "invalid_url_format"
        )

    if column_type == "ip_address":
        return "999.999.999.999", build_reason(
            column,
            "format_violation_case",
            "invalid_ip_address_format"
        )

    if column_type in ["date", "datetime", "timestamp"]:
        return "not-a-date", build_reason(
            column,
            "format_violation_case",
            "invalid_date_format"
        )

    if column_type == "boolean":
        return "not_boolean", build_reason(
            column,
            "format_violation_case",
            "invalid_boolean_format"
        )

    return "@@@###INVALID###@@@", build_reason(
        column,
        "format_violation_case",
        "invalid_generic_format"
    )


def generate_boundary_case_value(column):
    column_type = column.type.lower()

    if column_type in ["integer", "number", "decimal", "float", "currency_amount"]:
            is_integer_type = column_type in ["integer", "number"]

            if column.min is not None:
                boundary_value = int(column.min) if is_integer_type else column.min
                return boundary_value, build_reason(
                    column,
                    "boundary_case",
                    "minimum_boundary_value"
                )

            if column.max is not None:
                boundary_value = int(column.max) if is_integer_type else column.max
                return boundary_value, build_reason(
                    column,
                    "boundary_case",
                    "maximum_boundary_value"
                )

            return 0, build_reason(
                column,
                "boundary_case",
                "zero_boundary_value"
            )
    if column_type in ["string", "long_text"]:
        if column.max_length is not None:
            return "A" * column.max_length, build_reason(
                column,
                "boundary_case",
                "maximum_length_value"
            )

        if column.min_length is not None:
            return "A" * column.min_length, build_reason(
                column,
                "boundary_case",
                "minimum_length_value"
            )

        return "", build_reason(
            column,
            "boundary_case",
            "empty_string_boundary"
        )

    if column_type == "date":
        return str(date.today()), build_reason(
            column,
            "boundary_case",
            "today_date_boundary"
        )

    if column_type in ["datetime", "timestamp"]:
        return f"{date.today()}T00:00:00", build_reason(
            column,
            "boundary_case",
            "start_of_day_boundary"
        )

    if column_type == "category" and column.values:
        return column.values[0], build_reason(
            column,
            "boundary_case",
            "first_category_value"
        )

    return generate_normal_value(column, 0), build_reason(
        column,
        "boundary_case",
        "valid_boundary_like_value"
    )


def generate_corner_case_value(column):
    column_type = column.type.lower()

    if column_type in ["integer", "number", "decimal", "float", "currency_amount"]:
        candidates = [0, 1, -1]

        if column.min is not None:
            candidates.append(column.min + 1)

        if column.max is not None:
            candidates.append(column.max - 1)

        low = column.min if column.min is not None else float("-inf")
        high = column.max if column.max is not None else float("inf")
        valid_candidates = [x for x in candidates if low <= x <= high]

        if not valid_candidates:
            valid_candidates = [column.min if column.min is not None else 0]

        chosen = random.choice(valid_candidates)

        if column_type in ["integer", "number"]:
            chosen = int(chosen)

        return chosen, build_reason(
            column,
            "corner_case",
            "numeric_corner_value"
        )

    if column_type in ["string", "long_text", "name", "first_name", "last_name"]:
        return random.choice([" ", "A", "Test User", "测试डेटاテスト"]), build_reason(
            column,
            "corner_case",
            "string_corner_value"
        )

    if column_type == "date":
        return "2024-02-29", build_reason(
            column,
            "corner_case",
            "leap_year_date"
        )

    if column_type in ["datetime", "timestamp"]:
        return "2024-02-29T23:59:59", build_reason(
            column,
            "corner_case",
            "leap_year_datetime"
        )

    if column_type == "category" and column.values:
        return column.values[-1], build_reason(
            column,
            "corner_case",
            "last_category_value"
        )

    if column_type == "boolean":
        return True, build_reason(
            column,
            "corner_case",
            "boolean_true_corner"
        )

    return generate_normal_value(column, 0), build_reason(
        column,
        "corner_case",
        "valid_corner_like_value"
    )


def generate_invalid_case_value(column):
    column_type = column.type.lower()

    if column_type in ["integer", "number", "decimal", "float", "currency_amount"]:
        return "not_a_number", build_reason(
            column,
            "invalid_case",
            "invalid_numeric_value"
        )

    if column_type == "category":
        return "INVALID_CATEGORY", build_reason(
            column,
            "invalid_case",
            "invalid_category_value"
        )

    if column_type == "boolean":
        return "not_boolean", build_reason(
            column,
            "invalid_case",
            "invalid_boolean_value"
        )

    if column_type in ["date", "datetime", "timestamp"]:
        return "invalid-date", build_reason(
            column,
            "invalid_case",
            "invalid_date_value"
        )

    if column_type == "email":
        return "invalid-email", build_reason(
            column,
            "invalid_case",
            "invalid_email_value"
        )

    if column_type == "phone":
        return "123", build_reason(
            column,
            "invalid_case",
            "invalid_phone_value"
        )

    if column_type == "uuid":
        return "bad-uuid", build_reason(
            column,
            "invalid_case",
            "invalid_uuid_value"
        )

    if column_type == "url":
        return "bad-url", build_reason(
            column,
            "invalid_case",
            "invalid_url_value"
        )

    if column_type == "ip_address":
        return "999.999.999.999", build_reason(
            column,
            "invalid_case",
            "invalid_ip_address_value"
        )

    return "@@@INVALID@@@", build_reason(
        column,
        "invalid_case",
        "invalid_text_value"
    )


def generate_edge_case_value(column):
    column_type = column.type.lower()

    if column.nullable:
        return generate_null_case_value(column)

    if column_type in ["integer", "number", "decimal", "float", "currency_amount"]:
        return random.choice([0, -1, 999999999]), build_reason(
            column,
            "edge_case",
            "numeric_edge_value"
        )

    if column_type in ["string", "long_text", "name", "address", "company", "job_title"]:
        return random.choice(["", " ", "A" * 300, "@@@###$$$"]), build_reason(
            column,
            "edge_case",
            "text_edge_value"
        )

    if column_type == "email":
        return "missing-domain@", build_reason(
            column,
            "edge_case",
            "email_edge_value"
        )

    if column_type == "phone":
        return "0000000000", build_reason(
            column,
            "edge_case",
            "phone_edge_value"
        )

    if column_type == "date":
        return str(date.today() + timedelta(days=3650)), build_reason(
            column,
            "edge_case",
            "future_extreme_date"
        )

    if column_type in ["datetime", "timestamp"]:
        return f"{date.today() + timedelta(days=3650)}T00:00:00", build_reason(
            column,
            "edge_case",
            "future_extreme_datetime"
        )

    if column_type == "category":
        return "", build_reason(
            column,
            "edge_case",
            "empty_category_value"
        )

    value, _ = generate_invalid_case_value(column)
    return value, build_reason(
        column,
        "edge_case",
        "edge_not_applicable_used_invalid_value"
    )


def generate_duplicate_case_value(column, unique_trackers):
    existing_values = unique_trackers.get(column.name)

    if existing_values:
        existing_list = list(existing_values)

        if existing_list:
            return random.choice(existing_list), build_reason(
                column,
                "duplicate_case",
                "duplicate_existing_value"
            )

    return generate_normal_value(column, 0), build_reason(
        column,
        "duplicate_case",
        "no_existing_value_available"
    )


def generate_case_value(column, case_type, row_index, unique_trackers):
    if case_type == "null_case":
        return generate_null_case_value(column)

    if case_type == "range_violation_case":
        return generate_range_violation_value(column)

    if case_type == "length_violation_case":
        return generate_length_violation_value(column)

    if case_type == "format_violation_case":
        return generate_format_violation_value(column)

    if case_type == "boundary_case":
        return generate_boundary_case_value(column)

    if case_type == "corner_case":
        return generate_corner_case_value(column)

    if case_type == "invalid_case":
        return generate_invalid_case_value(column)

    if case_type == "edge_case":
        return generate_edge_case_value(column)

    if case_type == "duplicate_case":
        return generate_duplicate_case_value(column, unique_trackers)

    value = generate_normal_value(column, row_index)
    return value, None