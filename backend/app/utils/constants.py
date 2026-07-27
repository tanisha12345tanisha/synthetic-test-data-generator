SUPPORTED_DATA_TYPES = {
    "string",
    "integer",
    "number",
    "decimal",
    "float",
    "boolean",
    "date",
    "datetime",
    "timestamp",
    "category",
    "name",
    "first_name",
    "last_name",
    "email",
    "phone",
    "address",
    "city",
    "state",
    "country",
    "postal_code",
    "zip",
    "company",
    "job_title",
    "uuid",
    "id",
    "url",
    "ip_address",
    "currency_code",
    "currency_amount",
    "long_text",
    "regex"
}


SUPPORTED_DISTRIBUTIONS = {
    "uniform",
    "normal",
    "exponential",
    "weighted",
    "boolean_probability",
    "date_range"
}


CASE_LABELS = {
    "normal",
    "edge_case",
    "corner_case",
    "boundary_case",
    "invalid_case",
    "mixed_case",
    "duplicate_case",
    "null_case",
    "format_violation_case",
    "range_violation_case",
    "length_violation_case"
}


METADATA_COLUMNS = {
    "__case_type",
    "__case_labels",
    "__case_reasons"
}


SYNTHETIC_ONLY_POLICY = {
    "enabled": True,
    "message": "Generated data is synthetic only. Uploaded CSV files are used only for schema inference and should not be copied into generated output."
}