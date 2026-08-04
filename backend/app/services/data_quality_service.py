import random
import re
import ipaddress
import uuid
from datetime import datetime, date, timedelta
from urllib.parse import urlparse
import math
from app.reference_data.india_locations import INDIA_LOCATION_REFERENCE
from app.services.normal_generation_service import generate_normal_value


CITY_FIELD_NAMES = {
    "city",
    "town"
}

STATE_FIELD_NAMES = {
    "state",
    "province"
}

COUNTRY_FIELD_NAMES = {
    "country"
}

LOCALITY_FIELD_NAMES = {
    "locality",
    "area",
    "location",
    "neighbourhood",
    "neighborhood"
}

PINCODE_FIELD_NAMES = {
    "pincode",
    "pin_code",
    "pin",
    "postal_code",
    "zip",
    "zipcode",
    "zip_code"
}

ADDRESS_FIELD_NAMES = {
    "address",
    "addr",
    "street_address",
    "full_address"
}

FIRST_NAME_FIELD_NAMES = {
    "first_name",
    "firstname",
    "first"
}

LAST_NAME_FIELD_NAMES = {
    "last_name",
    "lastname",
    "surname",
    "last"
}

FULL_NAME_FIELD_NAMES = {
    "name",
    "full_name",
    "fullname",
    "customer_name",
    "person_name"
}

EMAIL_FIELD_NAMES = {
    "email",
    "email_id",
    "email_address"
}

PHONE_FIELD_NAMES = {
    "phone",
    "mobile",
    "mobile_number",
    "phone_number",
    "contact_number"
}

URL_FIELD_NAMES = {
    "url",
    "website",
    "link",
    "web_url"
}

IP_FIELD_NAMES = {
    "ip",
    "ip_address",
    "ipv4"
}

UUID_FIELD_NAMES = {
    "uuid",
    "guid"
}

AGE_FIELD_NAMES = {
    "age"
}

DOB_FIELD_NAMES = {
    "date_of_birth",
    "dob",
    "birth_date",
    "birthdate",
    "customer_dob"
}

CURRENCY_CODE_FIELD_NAMES = {
    "currency_code",
    "currency",
    "ccy"
}

STATUS_FIELD_NAMES = {
    "status",
    "account_status",
    "card_status",
    "customer_status",
    "user_status"
}

BOOLEAN_ACTIVE_FIELD_NAMES = {
    "is_active",
    "active",
    "enabled",
    "is_enabled"
}

NUMERIC_TYPES = {
    "integer",
    "number",
    "decimal",
    "float",
    "currency_amount"
}

INTEGER_TYPES = {
    "integer",
    "number"
}

TEXT_TYPES = {
    "string",
    "long_text",
    "name",
    "first_name",
    "last_name",
    "address",
    "company",
    "job_title"
}

METADATA_COLUMNS = {
    "__case_type",
    "__case_labels",
    "__case_reasons"
}

VALID_EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

JUNK_TEXT_VALUES = {
    "@@@invalid@@@",
    "@@@###invalid###@@@",
    "@@@###$$$",
    "invalid",
    "invalid_category",
    "not_a_number",
    "not_boolean",
    "bad-url",
    "bad-uuid",
    "invalid-date",
    "not-a-date",
    "not-a-url",
    "invalid-email"
}


def normalize_name(value):
    return str(value or "").strip().lower()


def get_column_attribute(column, attribute_name, default=None):
    if isinstance(column, dict):
        return column.get(attribute_name, default)

    return getattr(column, attribute_name, default)


def get_column_names(columns):
    return [
        get_column_attribute(column, "name")
        for column in columns
        if get_column_attribute(column, "name")
    ]


def get_user_column_names(columns):
    return [
        column_name
        for column_name in get_column_names(columns)
        if column_name not in METADATA_COLUMNS
    ]


def find_first_matching_field(column_names, allowed_names):
    for column_name in column_names:
        if normalize_name(column_name) in allowed_names:
            return column_name

    return None


def get_case_labels(row):
    labels = row.get("__case_labels", [])

    if not isinstance(labels, list):
        return []

    return labels


def should_skip_repair_for_case(row, skip_labels):
    labels = get_case_labels(row)

    return any(label in labels for label in skip_labels)


def should_preserve_intentional_invalid(row):
    return should_skip_repair_for_case(
        row,
        {
            "invalid_case",
            "format_violation_case",
            "range_violation_case",
            "length_violation_case",
            "duplicate_case",
            "null_case"
        }
    )


def infer_effective_type(column):
    column_name = normalize_name(get_column_attribute(column, "name"))
    column_type = normalize_name(get_column_attribute(column, "type"))

    if column_name in FIRST_NAME_FIELD_NAMES:
        return "first_name"

    if column_name in LAST_NAME_FIELD_NAMES:
        return "last_name"

    if column_name in FULL_NAME_FIELD_NAMES:
        return "name"

    if column_name in EMAIL_FIELD_NAMES or "email" in column_name:
        return "email"

    if column_name in PHONE_FIELD_NAMES or "phone" in column_name or "mobile" in column_name:
        return "phone"

    if column_name in URL_FIELD_NAMES or column_name.endswith("_url") or "website" in column_name:
        return "url"

    if column_name in IP_FIELD_NAMES or "ip_address" in column_name or column_name.endswith("_ip"):
        return "ip_address"

    if column_name in UUID_FIELD_NAMES or "uuid" in column_name or "guid" in column_name:
        return "uuid"

    if (
        column_name in PINCODE_FIELD_NAMES
        or "pincode" in column_name
        or "pin_code" in column_name
        or "postal" in column_name
        or column_name == "zip"
        or column_name == "zipcode"
        or column_name == "zip_code"
    ):
        return "postal_code"

    if "timestamp" in column_name:
        return "timestamp"

    if "datetime" in column_name:
        return "datetime"

    if column_name in DOB_FIELD_NAMES:
        return "date"

    if column_name.endswith("_date") or column_name == "date" or "date_value" in column_name:
        return "date"

    if column_name in CURRENCY_CODE_FIELD_NAMES or "currency_code" in column_name:
        return "currency_code"

    if "currency_amount" in column_name or "amount" in column_name:
        return "currency_amount"

    if column_name in AGE_FIELD_NAMES:
        return "integer"

    return column_type


def clean_first_name_word(value, fallback):
    text = str(value or "").replace(".", " ").replace("-", " ")
    words = re.findall(r"[A-Za-z]+", text)

    if words:
        return words[0].title()

    return fallback


def clean_last_name_word(value, fallback):
    text = str(value or "").replace(".", " ").replace("-", " ")
    words = re.findall(r"[A-Za-z]+", text)

    if words:
        return words[-1].title()

    return fallback


def email_token(value):
    token = re.sub(r"[^a-zA-Z0-9]", "", str(value or "").lower())

    if not token:
        return "user"

    return token


def build_consistent_email(first_name, last_name, row_index, used_emails):
    first_token = email_token(first_name)
    last_token = email_token(last_name)
    first_initial = first_token[0] if first_token else "u"

    domains = [
        "example.com",
        "example.net",
        "example.org",
        "testmail.com",
        "demo.in"
    ]

    patterns = [
        f"{first_token}.{last_token}",
        f"{first_token}{last_token}",
        f"{first_token}_{last_token}",
        f"{first_initial}.{last_token}",
        f"{first_initial}{last_token}",
        f"{last_token}.{first_token}",
        f"{first_token}{row_index + 1}",
        f"{first_token}.{last_token}{row_index + 1}"
    ]

    random.shuffle(patterns)
    random.shuffle(domains)

    for pattern in patterns:
        for domain in domains:
            email = f"{pattern}@{domain}"

            if email not in used_emails:
                used_emails.add(email)
                return email

    counter = row_index + 1
    fallback_email = f"{first_token}.{last_token}{counter}@example.com"

    while fallback_email in used_emails:
        counter += 1
        fallback_email = f"{first_token}.{last_token}{counter}@example.com"

    used_emails.add(fallback_email)

    return fallback_email


def generate_indian_phone():
    start_digit = random.choice(["6", "7", "8", "9"])
    remaining_digits = "".join(str(random.randint(0, 9)) for _ in range(9))

    return f"+91{start_digit}{remaining_digits}"


def is_valid_indian_phone(value):
    text = re.sub(r"\s+", "", str(value or ""))
    return bool(re.fullmatch(r"(\+91)?[6-9][0-9]{9}", text))


def is_valid_email(value):
    return bool(VALID_EMAIL_REGEX.fullmatch(str(value or "").strip()))


def is_valid_url(value):
    text = str(value or "").strip()

    if " " in text:
        return False

    parsed = urlparse(text)

    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_valid_ip(value):
    try:
        ipaddress.ip_address(str(value or "").strip())
        return True
    except ValueError:
        return False


def is_valid_uuid(value):
    try:
        uuid.UUID(str(value or "").strip())
        return True
    except ValueError:
        return False


def is_valid_date_value(value):
    try:
        datetime.strptime(str(value), "%Y-%m-%d").date()
        return True
    except ValueError:
        return False


def is_valid_datetime_value(value):
    try:
        datetime.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def parse_date_value(value):
    if value is None:
        return None

    if isinstance(value, date):
        return value

    text = str(value)

    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        pass

    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def is_valid_indian_pincode(value):
    return bool(re.fullmatch(r"[1-9][0-9]{5}", str(value or "").strip()))


def build_location_lookup():
    lookup = {}

    for location in INDIA_LOCATION_REFERENCE:
        city_key = normalize_name(location["city"])

        if city_key not in lookup:
            lookup[city_key] = []

        lookup[city_key].append(location)

    return lookup


def pick_location_for_row(row, city_field):
    location_lookup = build_location_lookup()

    if city_field and row.get(city_field):
        city_key = normalize_name(row.get(city_field))

        if city_key in location_lookup:
            return random.choice(location_lookup[city_key])

    return random.choice(INDIA_LOCATION_REFERENCE)


def build_address(location):
    house_number = random.randint(1, 999)
    street = random.choice(location["streets"])

    return (
        f"{house_number}, {street}, "
        f"{location['locality']}, "
        f"{location['city']}, "
        f"{location['state']} - "
        f"{location['pincode']}"
    )


def get_distribution_attribute(distribution, attribute_name, default=None):
    if isinstance(distribution, dict):
        return distribution.get(attribute_name, default)

    return getattr(distribution, attribute_name, default)


def generate_dob_from_age(age):
    today = date.today()
    birth_year = today.year - int(age)

    return date(birth_year, 7, 1).isoformat()


def calculate_age_from_dob(dob_value):
    dob = parse_date_value(dob_value)

    if not dob:
        return None

    today = date.today()
    age = today.year - dob.year

    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1

    return age


def generate_timestamp_value():
    generated_datetime = datetime(
        2025,
        random.randint(1, 12),
        random.randint(1, 28),
        random.randint(0, 23),
        random.randint(0, 59),
        random.randint(0, 59)
    )

    return generated_datetime.isoformat()


def generate_date_only_value():
    generated_date = date(
        2025,
        random.randint(1, 12),
        random.randint(1, 28)
    )

    return generated_date.isoformat()


def apply_indian_location_consistency(rows, columns):
    column_names = get_column_names(columns)

    city_field = find_first_matching_field(column_names, CITY_FIELD_NAMES)
    state_field = find_first_matching_field(column_names, STATE_FIELD_NAMES)
    country_field = find_first_matching_field(column_names, COUNTRY_FIELD_NAMES)
    locality_field = find_first_matching_field(column_names, LOCALITY_FIELD_NAMES)
    pincode_field = find_first_matching_field(column_names, PINCODE_FIELD_NAMES)
    address_field = find_first_matching_field(column_names, ADDRESS_FIELD_NAMES)

    location_fields = [
        city_field,
        state_field,
        country_field,
        locality_field,
        pincode_field,
        address_field
    ]

    existing_location_fields = [
        field
        for field in location_fields
        if field
    ]

    if len(existing_location_fields) < 2:
        return rows, {
            "rule": "indian_location_consistency",
            "status": "not_applicable",
            "fields_detected": existing_location_fields,
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row in rows:
        if should_skip_repair_for_case(row, {"invalid_case"}):
            continue

        location = pick_location_for_row(row, city_field)

        before_values = {
            field: row.get(field)
            for field in existing_location_fields
        }

        if city_field:
            row[city_field] = location["city"]

        if state_field:
            row[state_field] = location["state"]

        if country_field:
            row[country_field] = location["country"]

        if locality_field:
            row[locality_field] = location["locality"]

        if pincode_field:
            row[pincode_field] = location["pincode"]

        if address_field:
            row[address_field] = build_address(location)

        after_values = {
            field: row.get(field)
            for field in existing_location_fields
        }

        if before_values != after_values:
            repaired_rows += 1

        if pincode_field and not is_valid_indian_pincode(row.get(pincode_field)):
            failed_rows += 1

        if address_field and pincode_field:
            if str(row.get(pincode_field)) not in str(row.get(address_field)):
                failed_rows += 1

        if address_field and city_field:
            if str(row.get(city_field)) not in str(row.get(address_field)):
                failed_rows += 1

        if address_field and state_field:
            if str(row.get(state_field)) not in str(row.get(address_field)):
                failed_rows += 1

    return rows, {
        "rule": "indian_location_consistency",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": existing_location_fields,
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def apply_name_email_consistency(rows, columns):
    column_names = get_column_names(columns)

    first_name_field = find_first_matching_field(column_names, FIRST_NAME_FIELD_NAMES)
    last_name_field = find_first_matching_field(column_names, LAST_NAME_FIELD_NAMES)
    name_field = find_first_matching_field(column_names, FULL_NAME_FIELD_NAMES)
    email_field = find_first_matching_field(column_names, EMAIL_FIELD_NAMES)

    detected_fields = [
        field
        for field in [
            first_name_field,
            last_name_field,
            name_field,
            email_field
        ]
        if field
    ]

    if len(detected_fields) < 2:
        return rows, {
            "rule": "name_email_consistency",
            "status": "not_applicable",
            "fields_detected": detected_fields,
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0
    used_emails = set()

    for row_index, row in enumerate(rows):
        if should_skip_repair_for_case(
            row,
            {"invalid_case", "format_violation_case"}
        ):
            continue

        before_values = {
            field: row.get(field)
            for field in detected_fields
        }

        existing_first_name = row.get(first_name_field) if first_name_field else None
        existing_last_name = row.get(last_name_field) if last_name_field else None
        existing_full_name = row.get(name_field) if name_field else None

        if existing_first_name:
            first_name = clean_first_name_word(existing_first_name, "Aarav")
        elif existing_full_name:
            first_name = clean_first_name_word(existing_full_name, "Aarav")
        else:
            first_name = "Aarav"

        if existing_last_name:
            last_name = clean_last_name_word(existing_last_name, "Sharma")
        elif existing_full_name:
            last_name = clean_last_name_word(existing_full_name, "Sharma")
        else:
            last_name = "Sharma"

        if first_name_field:
            row[first_name_field] = first_name

        if last_name_field:
            row[last_name_field] = last_name

        if name_field:
            row[name_field] = f"{first_name} {last_name}"

        if email_field:
            row[email_field] = build_consistent_email(
                first_name=first_name,
                last_name=last_name,
                row_index=row_index,
                used_emails=used_emails
            )

        after_values = {
            field: row.get(field)
            for field in detected_fields
        }

        if before_values != after_values:
            repaired_rows += 1

        if first_name_field and len(str(row.get(first_name_field, "")).split()) != 1:
            failed_rows += 1

        if last_name_field and len(str(row.get(last_name_field, "")).split()) != 1:
            failed_rows += 1

        if name_field and len(str(row.get(name_field, "")).split()) != 2:
            failed_rows += 1

        if name_field and first_name_field and last_name_field:
            expected_name = f"{row.get(first_name_field)} {row.get(last_name_field)}"

            if row.get(name_field) != expected_name:
                failed_rows += 1

        if email_field and not is_valid_email(row.get(email_field)):
            failed_rows += 1

        if email_field:
            email_value = str(row.get(email_field, "")).lower()
            first_token = email_token(row.get(first_name_field) if first_name_field else first_name)
            last_token = email_token(row.get(last_name_field) if last_name_field else last_name)

            if first_token not in email_value and last_token not in email_value:
                failed_rows += 1

    return rows, {
        "rule": "name_email_consistency",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": detected_fields,
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_required_null_values(rows, columns):
    required_columns = [
        column
        for column in columns
        if get_column_attribute(column, "required", False)
    ]

    if not required_columns:
        return rows, {
            "rule": "required_field_not_null",
            "status": "not_applicable",
            "fields_detected": [],
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row_index, row in enumerate(rows):
        if should_skip_repair_for_case(row, {"null_case", "invalid_case"}):
            continue

        row_repaired = False
        row_failed = False

        for column in required_columns:
            column_name = get_column_attribute(column, "name")
            value = row.get(column_name)

            if value is None or str(value).strip() == "":
                repaired_value = generate_normal_value(column, row_index)

                if repaired_value is None or str(repaired_value).strip() == "":
                    row_failed = True
                else:
                    row[column_name] = repaired_value
                    row_repaired = True

        if row_repaired:
            repaired_rows += 1

        if row_failed:
            failed_rows += 1

    return rows, {
        "rule": "required_field_not_null",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": [
            get_column_attribute(column, "name")
            for column in required_columns
        ],
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_unique_values(rows, columns):
    unique_columns = [
        column
        for column in columns
        if get_column_attribute(column, "unique", False)
    ]

    if not unique_columns:
        return rows, {
            "rule": "unique_constraint",
            "status": "not_applicable",
            "fields_detected": [],
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for column in unique_columns:
        column_name = get_column_attribute(column, "name")
        seen_values = set()

        for row_index, row in enumerate(rows):
            value = row.get(column_name)

            if value is None:
                continue

            if value not in seen_values:
                seen_values.add(value)
                continue

            if should_skip_repair_for_case(row, {"duplicate_case"}):
                continue

            repaired_value = generate_normal_value(column, row_index)
            attempts = 0
            max_attempts = 100

            while repaired_value in seen_values and attempts < max_attempts:
                repaired_value = generate_normal_value(
                    column,
                    row_index + attempts + 1
                )
                attempts += 1

            if repaired_value in seen_values:
                repaired_value = f"{repaired_value}_{row_index + 1}_{attempts}"

            if repaired_value is None:
                failed_rows += 1
            else:
                row[column_name] = repaired_value
                seen_values.add(repaired_value)
                repaired_rows += 1

    return rows, {
        "rule": "unique_constraint",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": [
            get_column_attribute(column, "name")
            for column in unique_columns
        ],
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_numeric_ranges(rows, columns):
    numeric_columns = [
        column
        for column in columns
        if infer_effective_type(column) in NUMERIC_TYPES
    ]

    if not numeric_columns:
        return rows, {
            "rule": "numeric_range_consistency",
            "status": "not_applicable",
            "fields_detected": [],
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row in rows:
        if should_skip_repair_for_case(
            row,
            {"range_violation_case", "invalid_case"}
        ):
            continue

        row_repaired = False
        row_failed = False

        for column in numeric_columns:
            column_name = get_column_attribute(column, "name")
            column_type = infer_effective_type(column)
            min_value = get_column_attribute(column, "min")
            max_value = get_column_attribute(column, "max")
            value = row.get(column_name)

            if value is None:
                continue

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                if column_type == "currency_amount":
                    numeric_value = 0.0
                    row_repaired = True
                elif column_type == "integer":
                    numeric_value = 0
                    row_repaired = True
                else:
                    row_failed = True
                    continue

            if column_type == "currency_amount" and numeric_value < 0:
                numeric_value = abs(numeric_value)
                row_repaired = True

            if min_value is not None and numeric_value < min_value:
                numeric_value = min_value
                row_repaired = True

            if max_value is not None and numeric_value > max_value:
                numeric_value = max_value
                row_repaired = True

            if column_type in INTEGER_TYPES:
                numeric_value = int(round(numeric_value))
                # Re-clamp after rounding: a fractional bound (e.g. max=1.6)
                # can round up to 2, escaping the declared range.
                if min_value is not None:
                    numeric_value = max(numeric_value, math.ceil(min_value))
                if max_value is not None:
                    numeric_value = min(numeric_value, math.floor(max_value))

            if column_type in {"decimal", "float", "currency_amount"}:
                numeric_value = round(numeric_value, 2)

            if row.get(column_name) != numeric_value:
                row[column_name] = numeric_value
                row_repaired = True

        if row_repaired:
            repaired_rows += 1

        if row_failed:
            failed_rows += 1

    return rows, {
        "rule": "numeric_range_consistency",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": [
            get_column_attribute(column, "name")
            for column in numeric_columns
        ],
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_string_lengths_and_text_quality(rows, columns):
    text_columns = [
        column
        for column in columns
        if infer_effective_type(column) in TEXT_TYPES
    ]

    if not text_columns:
        return rows, {
            "rule": "text_quality_consistency",
            "status": "not_applicable",
            "fields_detected": [],
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row_index, row in enumerate(rows):
        if should_skip_repair_for_case(
            row,
            {"length_violation_case", "invalid_case"}
        ):
            continue

        row_repaired = False
        row_failed = False

        for column in text_columns:
            column_name = get_column_attribute(column, "name")
            min_length = get_column_attribute(column, "min_length")
            max_length = get_column_attribute(column, "max_length")
            value = row.get(column_name)

            if value is None:
                continue

            value = str(value)
            original_value = value
            normalized_value = normalize_name(value)

            if value.strip() == "" or normalized_value in JUNK_TEXT_VALUES:
                value = str(generate_normal_value(column, row_index))
                row_repaired = True

            if min_length is not None:
                while len(value) < min_length:
                    value += "X"

            if max_length is not None and len(value) > max_length:
                value = value[:max_length]

            if value != original_value:
                row[column_name] = value
                row_repaired = True

            if str(row.get(column_name, "")).strip() == "":
                row_failed = True

        if row_repaired:
            repaired_rows += 1

        if row_failed:
            failed_rows += 1

    return rows, {
        "rule": "text_quality_consistency",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": [
            get_column_attribute(column, "name")
            for column in text_columns
        ],
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_category_values(rows, columns):
    category_columns = [
        column
        for column in columns
        if infer_effective_type(column) == "category"
    ]

    if not category_columns:
        return rows, {
            "rule": "category_allowed_values",
            "status": "not_applicable",
            "fields_detected": [],
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row in rows:
        if should_skip_repair_for_case(row, {"invalid_case"}):
            continue

        row_repaired = False
        row_failed = False

        for column in category_columns:
            column_name = get_column_attribute(column, "name")
            allowed_values = get_column_attribute(column, "values", []) or []
            value = row.get(column_name)

            if value is None:
                continue

            if value not in allowed_values:
                if allowed_values:
                    row[column_name] = random.choice(allowed_values)
                    row_repaired = True
                else:
                    row_failed = True

        if row_repaired:
            repaired_rows += 1

        if row_failed:
            failed_rows += 1

    return rows, {
        "rule": "category_allowed_values",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": [
            get_column_attribute(column, "name")
            for column in category_columns
        ],
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_format_values(rows, columns):
    format_columns = [
        column
        for column in columns
        if infer_effective_type(column) in {
            "email",
            "phone",
            "url",
            "ip_address",
            "uuid",
            "date",
            "datetime",
            "timestamp",
            "postal_code",
            "zip"
        }
    ]

    if not format_columns:
        return rows, {
            "rule": "format_validation",
            "status": "not_applicable",
            "fields_detected": [],
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row_index, row in enumerate(rows):
        if should_skip_repair_for_case(row, {"invalid_case", "format_violation_case"}):
            continue

        row_repaired = False
        row_failed = False

        for column in format_columns:
            column_name = get_column_attribute(column, "name")
            effective_type = infer_effective_type(column)
            value = row.get(column_name)

            if value is None:
                continue

            if effective_type == "email" and not is_valid_email(value):
                row[column_name] = generate_normal_value(column, row_index)
                row_repaired = True

            elif effective_type == "phone" and not is_valid_indian_phone(value):
                row[column_name] = generate_indian_phone()
                row_repaired = True

            elif effective_type == "url" and not is_valid_url(value):
                row[column_name] = f"https://example.com/{row_index + 1}"
                row_repaired = True

            elif effective_type == "ip_address" and not is_valid_ip(value):
                row[column_name] = str(ipaddress.IPv4Address(3232235776 + row_index + 1))
                row_repaired = True

            elif effective_type == "uuid" and not is_valid_uuid(value):
                row[column_name] = str(uuid.uuid4())
                row_repaired = True

            elif effective_type == "date" and not is_valid_date_value(value):
                row[column_name] = generate_date_only_value()
                row_repaired = True

            elif effective_type in {"datetime", "timestamp"} and not is_valid_datetime_value(value):
                row[column_name] = generate_timestamp_value()
                row_repaired = True

            elif effective_type in {"postal_code", "zip"} and not is_valid_indian_pincode(value):
                row[column_name] = "560034"
                row_repaired = True

            repaired_value = row.get(column_name)

            if effective_type == "email" and not is_valid_email(repaired_value):
                row_failed = True

            elif effective_type == "phone" and not is_valid_indian_phone(repaired_value):
                row_failed = True

            elif effective_type == "url" and not is_valid_url(repaired_value):
                row_failed = True

            elif effective_type == "ip_address" and not is_valid_ip(repaired_value):
                row_failed = True

            elif effective_type == "uuid" and not is_valid_uuid(repaired_value):
                row_failed = True

            elif effective_type == "date" and not is_valid_date_value(repaired_value):
                row_failed = True

            elif effective_type in {"datetime", "timestamp"} and not is_valid_datetime_value(repaired_value):
                row_failed = True

            elif effective_type in {"postal_code", "zip"} and not is_valid_indian_pincode(repaired_value):
                row_failed = True

        if row_repaired:
            repaired_rows += 1

        if row_failed:
            failed_rows += 1

    return rows, {
        "rule": "format_validation",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": [
            get_column_attribute(column, "name")
            for column in format_columns
        ],
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_date_ranges(rows, columns):
    date_columns = []

    for column in columns:
        effective_type = infer_effective_type(column)

        if effective_type not in {"date", "datetime", "timestamp"}:
            continue

        distribution = get_column_attribute(column, "distribution")

        if not distribution:
            continue

        distribution_type = normalize_name(
            get_distribution_attribute(distribution, "type")
        )

        if distribution_type == "date_range":
            date_columns.append(column)

    if not date_columns:
        return rows, {
            "rule": "date_range_consistency",
            "status": "not_applicable",
            "fields_detected": [],
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row in rows:
        if should_skip_repair_for_case(row, {"invalid_case", "format_violation_case"}):
            continue

        row_repaired = False
        row_failed = False

        for column in date_columns:
            column_name = get_column_attribute(column, "name")
            effective_type = infer_effective_type(column)
            distribution = get_column_attribute(column, "distribution")

            start = parse_date_value(
                get_distribution_attribute(distribution, "start_date")
            )
            end = parse_date_value(
                get_distribution_attribute(distribution, "end_date")
            )
            current_value = parse_date_value(row.get(column_name))

            if not start or not end:
                row_failed = True
                continue

            if current_value is None or current_value < start or current_value > end:
                days_between = (end - start).days
                new_date = start + timedelta(days=random.randint(0, days_between))

                if effective_type == "date":
                    row[column_name] = new_date.isoformat()
                else:
                    row[column_name] = datetime(
                        new_date.year,
                        new_date.month,
                        new_date.day,
                        random.randint(0, 23),
                        random.randint(0, 59),
                        random.randint(0, 59)
                    ).isoformat()

                row_repaired = True

        if row_repaired:
            repaired_rows += 1

        if row_failed:
            failed_rows += 1

    return rows, {
        "rule": "date_range_consistency",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": [
            get_column_attribute(column, "name")
            for column in date_columns
        ],
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_age_dob_consistency(rows, columns):
    column_names = get_column_names(columns)

    age_field = find_first_matching_field(column_names, AGE_FIELD_NAMES)
    dob_field = find_first_matching_field(column_names, DOB_FIELD_NAMES)

    detected_fields = [
        field
        for field in [age_field, dob_field]
        if field
    ]

    if len(detected_fields) < 2:
        return rows, {
            "rule": "age_dob_consistency",
            "status": "not_applicable",
            "fields_detected": detected_fields,
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row in rows:
        if should_preserve_intentional_invalid(row):
            continue

        row_repaired = False

        try:
            age = int(float(row.get(age_field)))
        except (TypeError, ValueError):
            age = random.randint(18, 70)
            row[age_field] = age
            row_repaired = True

        if age < 0:
            age = abs(age)
            row[age_field] = age
            row_repaired = True

        if age > 100:
            age = 100
            row[age_field] = age
            row_repaired = True

        calculated_age = calculate_age_from_dob(row.get(dob_field))

        if calculated_age is None or abs(calculated_age - age) > 1:
            row[dob_field] = generate_dob_from_age(age)
            row_repaired = True

        final_calculated_age = calculate_age_from_dob(row.get(dob_field))

        if final_calculated_age is None or abs(final_calculated_age - age) > 1:
            failed_rows += 1

        if row_repaired:
            repaired_rows += 1

    return rows, {
        "rule": "age_dob_consistency",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": detected_fields,
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_country_currency_consistency(rows, columns):
    column_names = get_column_names(columns)

    country_field = find_first_matching_field(column_names, COUNTRY_FIELD_NAMES)
    currency_field = find_first_matching_field(column_names, CURRENCY_CODE_FIELD_NAMES)

    detected_fields = [
        field
        for field in [country_field, currency_field]
        if field
    ]

    if len(detected_fields) < 2:
        return rows, {
            "rule": "country_currency_consistency",
            "status": "not_applicable",
            "fields_detected": detected_fields,
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row in rows:
        if should_preserve_intentional_invalid(row):
            continue

        before_values = {
            field: row.get(field)
            for field in detected_fields
        }

        row[country_field] = "India"
        row[currency_field] = "INR"

        after_values = {
            field: row.get(field)
            for field in detected_fields
        }

        if before_values != after_values:
            repaired_rows += 1

        if row.get(country_field) != "India" or row.get(currency_field) != "INR":
            failed_rows += 1

    return rows, {
        "rule": "country_currency_consistency",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": detected_fields,
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_status_boolean_consistency(rows, columns):
    column_names = get_column_names(columns)

    status_field = find_first_matching_field(column_names, STATUS_FIELD_NAMES)
    active_field = find_first_matching_field(column_names, BOOLEAN_ACTIVE_FIELD_NAMES)

    detected_fields = [
        field
        for field in [status_field, active_field]
        if field
    ]

    if len(detected_fields) < 2:
        return rows, {
            "rule": "status_boolean_consistency",
            "status": "not_applicable",
            "fields_detected": detected_fields,
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    true_statuses = {
        "active",
        "open",
        "enabled"
    }

    false_statuses = {
        "inactive",
        "closed",
        "blocked",
        "disabled"
    }

    repaired_rows = 0
    failed_rows = 0

    for row in rows:
        if should_preserve_intentional_invalid(row):
            continue

        status_value = normalize_name(row.get(status_field))

        if status_value in true_statuses:
            expected_value = True
        elif status_value in false_statuses:
            expected_value = False
        else:
            continue

        if row.get(active_field) != expected_value:
            row[active_field] = expected_value
            repaired_rows += 1

        if row.get(active_field) != expected_value:
            failed_rows += 1

    return rows, {
        "rule": "status_boolean_consistency",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": detected_fields,
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_regex_values(rows, columns):
    regex_columns = [
        column
        for column in columns
        if infer_effective_type(column) == "regex"
    ]

    if not regex_columns:
        return rows, {
            "rule": "regex_pattern_consistency",
            "status": "not_applicable",
            "fields_detected": [],
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repaired_rows = 0
    failed_rows = 0

    for row_index, row in enumerate(rows):
        if should_skip_repair_for_case(row, {"invalid_case", "format_violation_case"}):
            continue

        row_repaired = False
        row_failed = False

        for column in regex_columns:
            column_name = get_column_attribute(column, "name")
            pattern = get_column_attribute(column, "pattern")
            value = row.get(column_name)

            if not pattern:
                row_failed = True
                continue

            try:
                if value is None or not re.fullmatch(pattern, str(value)):
                    row[column_name] = generate_normal_value(column, row_index)
                    row_repaired = True

                if not re.fullmatch(pattern, str(row.get(column_name))):
                    row_failed = True

            except re.error:
                row[column_name] = "REGEX_VALUE_001"
                row_repaired = True

        if row_repaired:
            repaired_rows += 1

        if row_failed:
            failed_rows += 1

    return rows, {
        "rule": "regex_pattern_consistency",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": [
            get_column_attribute(column, "name")
            for column in regex_columns
        ],
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def repair_duplicate_rows(rows, columns):
    user_column_names = get_user_column_names(columns)

    if len(user_column_names) < 2:
        return rows, {
            "rule": "duplicate_row_detection",
            "status": "not_applicable",
            "fields_detected": user_column_names,
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    repairable_columns = [
        column
        for column in columns
        if get_column_attribute(column, "name") in user_column_names
        and infer_effective_type(column) not in {
            "city",
            "state",
            "country",
            "postal_code",
            "zip",
            "address"
        }
    ]

    if not repairable_columns:
        return rows, {
            "rule": "duplicate_row_detection",
            "status": "not_applicable",
            "fields_detected": user_column_names,
            "rows_checked": 0,
            "rows_repaired": 0,
            "failed_rows": 0
        }

    seen_rows = set()
    repaired_rows = 0
    failed_rows = 0

    for row_index, row in enumerate(rows):
        row_signature = tuple(
            str(row.get(column_name))
            for column_name in user_column_names
        )

        if row_signature not in seen_rows:
            seen_rows.add(row_signature)
            continue

        if should_skip_repair_for_case(row, {"duplicate_case"}):
            continue

        target_column = repairable_columns[0]
        target_column_name = get_column_attribute(target_column, "name")
        row[target_column_name] = generate_normal_value(target_column, row_index)

        new_signature = tuple(
            str(row.get(column_name))
            for column_name in user_column_names
        )

        if new_signature in seen_rows:
            failed_rows += 1
        else:
            seen_rows.add(new_signature)
            repaired_rows += 1

    return rows, {
        "rule": "duplicate_row_detection",
        "status": "pass" if failed_rows == 0 else "fail",
        "fields_detected": user_column_names,
        "rows_checked": len(rows),
        "rows_repaired": repaired_rows,
        "failed_rows": failed_rows
    }


def build_quality_report(checks):
    applicable_checks = [
        check
        for check in checks
        if check.get("status") != "not_applicable"
    ]

    failed_checks = [
        check
        for check in applicable_checks
        if check.get("status") == "fail"
    ]

    total_checks = len(applicable_checks)
    failed_count = len(failed_checks)
    passed_count = total_checks - failed_count

    if total_checks == 0:
        overall_score = 100
    else:
        overall_score = round((passed_count / total_checks) * 100, 2)

    return {
        "overall_score": overall_score,
        "rules_checked": total_checks,
        "rules_passed": passed_count,
        "rules_failed": failed_count,
        "checks": checks
    }


def apply_data_quality_rules(rows, columns):
    checks = []

    rows, location_check = apply_indian_location_consistency(
        rows=rows,
        columns=columns
    )
    checks.append(location_check)

    rows, name_email_check = apply_name_email_consistency(
        rows=rows,
        columns=columns
    )
    checks.append(name_email_check)

    rows, required_check = repair_required_null_values(
        rows=rows,
        columns=columns
    )
    checks.append(required_check)

    rows, unique_check = repair_unique_values(
        rows=rows,
        columns=columns
    )
    checks.append(unique_check)

    rows, numeric_check = repair_numeric_ranges(
        rows=rows,
        columns=columns
    )
    checks.append(numeric_check)

    rows, text_check = repair_string_lengths_and_text_quality(
        rows=rows,
        columns=columns
    )
    checks.append(text_check)

    rows, category_check = repair_category_values(
        rows=rows,
        columns=columns
    )
    checks.append(category_check)

    rows, format_check = repair_format_values(
        rows=rows,
        columns=columns
    )
    checks.append(format_check)

    rows, date_range_check = repair_date_ranges(
        rows=rows,
        columns=columns
    )
    checks.append(date_range_check)

    rows, age_dob_check = repair_age_dob_consistency(
        rows=rows,
        columns=columns
    )
    checks.append(age_dob_check)

    rows, country_currency_check = repair_country_currency_consistency(
        rows=rows,
        columns=columns
    )
    checks.append(country_currency_check)

    rows, status_boolean_check = repair_status_boolean_consistency(
        rows=rows,
        columns=columns
    )
    checks.append(status_boolean_check)

    rows, regex_check = repair_regex_values(
        rows=rows,
        columns=columns
    )
    checks.append(regex_check)

    rows, duplicate_row_check = repair_duplicate_rows(
        rows=rows,
        columns=columns
    )
    checks.append(duplicate_row_check)

    quality_report = build_quality_report(checks)

    return rows, quality_report