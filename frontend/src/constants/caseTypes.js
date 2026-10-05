export const CASE_PERCENTAGE_FIELDS = [
  {
    key: "normal",
    label: "Normal",
    description: "Valid standard rows",
  },
  {
    key: "edge_case",
    label: "Edge case",
    description: "Extreme but useful test values",
  },
  {
    key: "corner_case",
    label: "Corner case",
    description: "Special boundary-like data",
  },
  {
    key: "boundary_case",
    label: "Boundary case",
    description: "Min/max and boundary values",
  },
  {
    key: "invalid_case",
    label: "Invalid case",
    description: "Clearly invalid values",
  },
  {
    key: "duplicate_case",
    label: "Duplicate case",
    description: "Duplicate unique fields",
  },
  {
    key: "null_case",
    label: "Null case",
    description: "Null values for testing",
  },
  {
    key: "format_violation_case",
    label: "Format violation",
    description: "Invalid email, phone, date, etc.",
  },
  {
    key: "range_violation_case",
    label: "Range violation",
    description: "Values below min or above max",
  },
  {
    key: "length_violation_case",
    label: "Length violation",
    description: "Text below/above allowed length",
  },
]

export const DEFAULT_CASE_DISTRIBUTION = {
  normal: 70,
  edge_case: 10,
  corner_case: 5,
  boundary_case: 5,
  invalid_case: 5,
  duplicate_case: 1,
  null_case: 1,
  format_violation_case: 1,
  range_violation_case: 1,
  length_violation_case: 1,
}