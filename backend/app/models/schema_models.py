from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from app.utils.constants import (
    SUPPORTED_DATA_TYPES,
    SUPPORTED_DISTRIBUTIONS,
    METADATA_COLUMNS
)
from datetime import datetime


LENGTH_SUPPORTED_TYPES = {"string", "name", "first_name", "last_name", "long_text"}


class DistributionConfig(BaseModel):
    type: str = Field(
        default="uniform",
        description="Distribution type: uniform, normal, exponential, weighted, boolean_probability, date_range"
    )
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    weights: Optional[Dict[str, float]] = None
    true_probability: Optional[float] = Field(default=None, ge=0, le=100)
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @model_validator(mode="after")
    def validate_distribution_config(self):
        normalized_type = self.type.lower()

        if normalized_type not in SUPPORTED_DISTRIBUTIONS:
            raise ValueError(
                f"Unsupported distribution type '{self.type}'. "
                f"Supported distributions are: {sorted(SUPPORTED_DISTRIBUTIONS)}"
            )

        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("Distribution min cannot be greater than distribution max.")

        if normalized_type == "normal":
            if self.std is not None and self.std <= 0:
                raise ValueError("Normal distribution std must be greater than 0.")

        if normalized_type == "weighted":
            if not self.weights:
                raise ValueError("Weighted distribution requires weights.")

            if any(weight < 0 for weight in self.weights.values()):
                raise ValueError("Weighted distribution weights cannot be negative.")

            if sum(self.weights.values()) <= 0:
                raise ValueError("Weighted distribution weights must sum to more than 0.")

        if normalized_type == "date_range":
            if not self.start_date or not self.end_date:
                raise ValueError("Date range distribution requires start_date and end_date.")

            start = self._parse_strict_date(self.start_date)
            end = self._parse_strict_date(self.end_date)

            if start > end:
                raise ValueError("Date range start_date cannot be after end_date.")

        return self

    @staticmethod
    def _parse_strict_date(value: str):
        """Parse a date that must be EXACTLY YYYY-MM-DD (4-digit year,
        zero-padded month and day). strptime alone is too lenient (it accepts
        '2020-1-1'), so we enforce the shape before parsing."""
        import re

        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Date range must use YYYY-MM-DD format.")

        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date range must use YYYY-MM-DD format.")


class CaseDistributionConfig(BaseModel):
    normal: int = Field(default=70, ge=0, le=100)
    edge_case: int = Field(default=10, ge=0, le=100)
    corner_case: int = Field(default=5, ge=0, le=100)
    boundary_case: int = Field(default=5, ge=0, le=100)
    invalid_case: int = Field(default=5, ge=0, le=100)
    duplicate_case: int = Field(default=1, ge=0, le=100)
    null_case: int = Field(default=1, ge=0, le=100)
    format_violation_case: int = Field(default=1, ge=0, le=100)
    range_violation_case: int = Field(default=1, ge=0, le=100)
    length_violation_case: int = Field(default=1, ge=0, le=100)

    @model_validator(mode="after")
    def validate_total_percentage(self):
        total = (
            self.normal
            + self.edge_case
            + self.corner_case
            + self.boundary_case
            + self.invalid_case
            + self.duplicate_case
            + self.null_case
            + self.format_violation_case
            + self.range_violation_case
            + self.length_violation_case
        )

        if total != 100:
            raise ValueError(
                f"Case distribution percentages must total 100. Current total is {total}."
            )

        return self


class ColumnSchema(BaseModel):
    name: str
    type: str
    required: bool = True
    nullable: bool = False
    unique: bool = False
    min: Optional[float] = None
    max: Optional[float] = None
    min_length: Optional[int] = Field(default=None, ge=0)
    max_length: Optional[int] = Field(default=None, ge=0)
    values: Optional[List[Any]] = None
    prefix: Optional[str] = None
    pattern: Optional[str] = None
    distribution: Optional[DistributionConfig] = None

    @model_validator(mode="after")
    def validate_column_config(self):
        if not self.name or not self.name.strip():
            raise ValueError("Column name cannot be empty.")

        if self.name.strip() in METADATA_COLUMNS:
            raise ValueError(
                f"Column name '{self.name}' is reserved for system metadata and cannot be used."
            )

        normalized_type = self.type.lower()

        if normalized_type not in SUPPORTED_DATA_TYPES:
            raise ValueError(
                f"Unsupported column type '{self.type}'. "
                f"Supported types are: {sorted(SUPPORTED_DATA_TYPES)}"
            )

        if (
            self.min_length is not None or self.max_length is not None
        ) and normalized_type not in LENGTH_SUPPORTED_TYPES:
            raise ValueError(
                f"Column '{self.name}' of type '{self.type}' does not support length "
                f"constraints. min_length/max_length are only valid for: "
                f"{sorted(LENGTH_SUPPORTED_TYPES)}"
            )

        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(
                f"Column '{self.name}' has invalid numeric range: min cannot be greater than max."
            )

        if (
            self.min_length is not None
            and self.max_length is not None
            and self.min_length > self.max_length
        ):
            raise ValueError(
                f"Column '{self.name}' has invalid length range: min_length cannot be greater than max_length."
            )

        if normalized_type == "category" and not self.values:
            raise ValueError(
                f"Column '{self.name}' is category type and must have allowed values."
            )

        if normalized_type == "category" and self.distribution:
            if self.distribution.type.lower() == "weighted":
                weight_keys = set(self.distribution.weights.keys()) if self.distribution.weights else set()
                value_keys = set(str(value) for value in self.values)
                missing_weights = value_keys - weight_keys

                if missing_weights:
                    raise ValueError(
                        f"Column '{self.name}' has category values without weights: {sorted(missing_weights)}"
                    )

        if normalized_type == "id" and not self.prefix:
            raise ValueError(
                f"Column '{self.name}' is id type and must have a prefix."
            )

        if normalized_type == "regex" and not self.pattern:
            raise ValueError(
                f"Column '{self.name}' is regex type and must have a pattern."
            )

        return self


class DatasetRequest(BaseModel):
    dataset_name: str
    row_count: int = Field(ge=1, le=10000)
    seed: Optional[int] = None
    columns: List[ColumnSchema]
    case_distribution: CaseDistributionConfig = CaseDistributionConfig()

    @model_validator(mode="after")
    def validate_dataset_request(self):
        if not self.dataset_name or not self.dataset_name.strip():
            raise ValueError("Dataset name cannot be empty.")

        if not self.columns:
            raise ValueError("At least one column is required.")

        column_names = [
            column.name.strip().lower()
            for column in self.columns
        ]

        if len(column_names) != len(set(column_names)):
            raise ValueError("Duplicate column names are not allowed.")

        return self


class CaseReason(BaseModel):
    column: str
    label: str
    reason: str


class QualityCheck(BaseModel):
    rule: str
    status: str
    fields_detected: Optional[List[str]] = None
    rows_checked: int = 0
    rows_repaired: int = 0
    failed_rows: int = 0


class QualityReport(BaseModel):
    overall_score: float
    rules_checked: int
    rules_passed: int
    rules_failed: int
    checks: List[Dict[str, Any]]


class DatasetSummary(BaseModel):
    dataset_name: str
    total_rows: int
    total_columns: int
    seed: Optional[int]
    synthetic_only: bool
    preview_recommended_rows: int

    normal_rows: int
    edge_case_rows: int
    corner_case_rows: int
    boundary_case_rows: int
    invalid_case_rows: int
    duplicate_case_rows: int
    null_case_rows: int
    format_violation_case_rows: int
    range_violation_case_rows: int
    length_violation_case_rows: int

    data_quality_score: Optional[float] = None
    data_quality_rules_checked: Optional[int] = None
    data_quality_rules_passed: Optional[int] = None
    data_quality_rules_failed: Optional[int] = None


class DatasetResponse(BaseModel):
    dataset_name: str
    row_count: int
    generated_rows: List[Dict[str, Any]]
    summary: DatasetSummary
    quality_report: Optional[QualityReport] = None