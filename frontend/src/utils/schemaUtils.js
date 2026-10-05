import {
  RESERVED_COLUMN_NAMES,
  supportsBooleanProbability,
  supportsCategoryValues,
  supportsDateRange,
  supportsLengthRange,
  supportsNumericRange,
  supportsPattern,
  supportsPrefix
} from "../constants/dataTypes"


export function createEmptyColumn() {
  return {
    id: crypto.randomUUID(),
    name: "",
    type: "",
    required: false,
    nullable: false,
    unique: false,
    min: "",
    max: "",
    min_length: "",
    max_length: "",
    values: "",
    prefix: "",
    pattern: "",
    distribution_type: "",
    mean: "",
    std: "",
    true_probability: "",
    start_date: "",
    end_date: "",
    weights: ""
  }
}


export function parseWeights(weightsText) {
  const weights = {}

  weightsText
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .forEach((item) => {
      const [key, value] = item
        .split(":")
        .map((part) => part.trim())

      if (key && value !== undefined && value !== "") {
        weights[key] = Number(value)
      }
    })

  return weights
}


export function convertInferredColumnsToFrontendColumns(inferredColumns) {
  return inferredColumns
    .filter((column) => !RESERVED_COLUMN_NAMES.has(column.name))
    .map((column) => ({
      id: crypto.randomUUID(),
      name: column.name || "",
      type: column.type || "string",
      required: Boolean(column.required),
      nullable: Boolean(column.nullable),
      unique: Boolean(column.unique),
      min:
        column.min !== null && column.min !== undefined
          ? String(column.min)
          : "",
      max:
        column.max !== null && column.max !== undefined
          ? String(column.max)
          : "",
      min_length:
        column.min_length !== null && column.min_length !== undefined
          ? String(column.min_length)
          : "",
      max_length:
        column.max_length !== null && column.max_length !== undefined
          ? String(column.max_length)
          : "",
      values: Array.isArray(column.values)
        ? column.values.join(",")
        : "",
      prefix: column.prefix || "",
      pattern: column.pattern || "",
      distribution_type: column.distribution?.type || "",
      mean:
        column.distribution?.mean !== null &&
        column.distribution?.mean !== undefined
          ? String(column.distribution.mean)
          : "",
      std:
        column.distribution?.std !== null &&
        column.distribution?.std !== undefined
          ? String(column.distribution.std)
          : "",
      true_probability:
        column.distribution?.true_probability !== null &&
        column.distribution?.true_probability !== undefined
          ? String(column.distribution.true_probability)
          : "",
      start_date: column.distribution?.start_date || "",
      end_date: column.distribution?.end_date || "",
      weights: column.distribution?.weights
        ? Object.entries(column.distribution.weights)
            .map(([key, value]) => `${key}:${value}`)
            .join(",")
        : ""
    }))
}


export function buildSchemaPreview({
  datasetName,
  rowCount,
  columns,
  caseDistribution
}) {
  return {
    dataset_name: datasetName.trim(),
    row_count: Number(rowCount),
    columns: columns.map((column) => {
      const schemaColumn = {
        name: column.name.trim(),
        type: column.type,
        required: column.required,
        nullable: column.nullable,
        unique: column.unique
      }

      if (supportsNumericRange(column.type)) {
        if (column.min !== "") {
          schemaColumn.min = Number(column.min)
        }

        if (column.max !== "") {
          schemaColumn.max = Number(column.max)
        }
      }

      if (supportsLengthRange(column.type)) {
        if (column.min_length !== "") {
          schemaColumn.min_length = Number(column.min_length)
        }

        if (column.max_length !== "") {
          schemaColumn.max_length = Number(column.max_length)
        }
      }

      if (
        supportsCategoryValues(column.type) &&
        column.values.trim() !== ""
      ) {
        schemaColumn.values = column.values
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean)
      }

      if (
        supportsPrefix(column.type) &&
        column.prefix.trim() !== ""
      ) {
        schemaColumn.prefix = column.prefix.trim()
      }

      if (
        supportsPattern(column.type) &&
        column.pattern.trim() !== ""
      ) {
        schemaColumn.pattern = column.pattern.trim()
      }

      if (
        supportsNumericRange(column.type) &&
        column.distribution_type
      ) {
        if (column.distribution_type === "uniform") {
          schemaColumn.distribution = {
            type: "uniform"
          }

          if (column.min !== "") {
            schemaColumn.distribution.min = Number(column.min)
          }

          if (column.max !== "") {
            schemaColumn.distribution.max = Number(column.max)
          }
        }

        if (column.distribution_type === "normal") {
          schemaColumn.distribution = {
            type: "normal"
          }

          if (column.mean !== "") {
            schemaColumn.distribution.mean = Number(column.mean)
          }

          if (column.std !== "") {
            schemaColumn.distribution.std = Number(column.std)
          }
        }

        if (column.distribution_type === "exponential") {
          schemaColumn.distribution = {
            type: "exponential"
          }

          if (column.mean !== "") {
            schemaColumn.distribution.mean = Number(column.mean)
          }
        }
      }

      if (
        supportsBooleanProbability(column.type) &&
        column.true_probability !== ""
      ) {
        schemaColumn.distribution = {
          type: "boolean_probability",
          true_probability: Number(column.true_probability)
        }
      }

      if (
        supportsDateRange(column.type) &&
        column.start_date &&
        column.end_date
      ) {
        schemaColumn.distribution = {
          type: "date_range",
          start_date: column.start_date,
          end_date: column.end_date
        }
      }

      if (
        supportsCategoryValues(column.type) &&
        column.weights.trim() !== ""
      ) {
        schemaColumn.distribution = {
          type: "weighted",
          weights: parseWeights(column.weights)
        }
      }

      return schemaColumn
    }),
    case_distribution: caseDistribution
  }
}