import {
  RESERVED_COLUMN_NAMES,
  supportsBooleanProbability,
  supportsCategoryValues,
  supportsDateRange
} from "../constants/dataTypes"

import { parseWeights } from "./schemaUtils"


function validateRequiredColumnFields(column) {
  if (!column.name.trim()) {
    return "Every column must have a name."
  }

  if (!column.type.trim()) {
    return `Please select a data type for column "${
      column.name || "Unnamed column"
    }".`
  }

  if (RESERVED_COLUMN_NAMES.has(column.name.trim())) {
    return `${column.name} is reserved for system metadata.`
  }

  return ""
}


function validateColumnTypeConfiguration(column) {
  if (column.type === "id" && !column.prefix.trim()) {
    return `ID column "${column.name}" must have a prefix.`
  }

  if (column.type === "category" && !column.values.trim()) {
    return `Category column "${column.name}" must have comma-separated values.`
  }

  if (column.type === "regex" && !column.pattern.trim()) {
    return `Regex column "${column.name}" must have a pattern.`
  }

  return ""
}


function validateNumericRange(column) {
  if (column.min === "" || column.max === "") {
    return ""
  }

  const minValue = Number(column.min)
  const maxValue = Number(column.max)

  if (minValue > maxValue) {
    return `Column "${column.name}" has min greater than max.`
  }

  return ""
}


function validateLengthRange(column) {
  if (column.min_length === "" || column.max_length === "") {
    return ""
  }

  const minLength = Number(column.min_length)
  const maxLength = Number(column.max_length)

  if (minLength > maxLength) {
    return `Column "${column.name}" has min length greater than max length.`
  }

  return ""
}


function validateBooleanProbability(column) {
  if (
    !supportsBooleanProbability(column.type) ||
    column.true_probability === ""
  ) {
    return ""
  }

  const probability = Number(column.true_probability)

  if (
    Number.isNaN(probability) ||
    probability < 0 ||
    probability > 100
  ) {
    return `True probability for column "${column.name}" must be between 0 and 100.`
  }

  return ""
}


function validateDateRange(column) {
  if (!supportsDateRange(column.type)) {
    return ""
  }

  const hasStartDate = Boolean(column.start_date)
  const hasEndDate = Boolean(column.end_date)

  if (
    (hasStartDate && !hasEndDate) ||
    (!hasStartDate && hasEndDate)
  ) {
    return `Date range for column "${column.name}" requires both start date and end date.`
  }

  if (
    hasStartDate &&
    hasEndDate &&
    column.start_date > column.end_date
  ) {
    return `Start date cannot be after end date for column "${column.name}".`
  }

  return ""
}


function validateCategoryWeights(column) {
  if (
    !supportsCategoryValues(column.type) ||
    column.weights.trim() === ""
  ) {
    return ""
  }

  const parsedWeights = parseWeights(column.weights)

  if (Object.keys(parsedWeights).length === 0) {
    return `Weights for category column "${column.name}" must use format value:weight.`
  }

  const hasInvalidWeight = Object.values(parsedWeights).some(
    (value) => Number.isNaN(Number(value))
  )

  if (hasInvalidWeight) {
    return `Weights for category column "${column.name}" must be numeric.`
  }

  const totalWeight = Object.values(parsedWeights).reduce(
    (total, value) => total + Number(value || 0),
    0
  )

  if (totalWeight <= 0) {
    return `Weights for category column "${column.name}" must sum to more than 0.`
  }

  const categoryValues = column.values
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)

  const weightKeys = Object.keys(parsedWeights)

  const missingWeights = categoryValues.filter(
    (value) => !weightKeys.includes(value)
  )

  if (missingWeights.length > 0) {
    return `Weights missing for category values: ${missingWeights.join(", ")}.`
  }

  return ""
}


function validateDistribution(column) {
  if (
    column.distribution_type === "normal" &&
    column.std !== "" &&
    Number(column.std) <= 0
  ) {
    return `Standard deviation for column "${column.name}" must be greater than 0.`
  }

  return ""
}


function validateColumn(column) {
  const validators = [
    validateRequiredColumnFields,
    validateColumnTypeConfiguration,
    validateNumericRange,
    validateLengthRange,
    validateBooleanProbability,
    validateDateRange,
    validateCategoryWeights,
    validateDistribution
  ]

  for (const validator of validators) {
    const validationError = validator(column)

    if (validationError) {
      return validationError
    }
  }

  return ""
}


export function validateSchema(columns) {
  if (!Array.isArray(columns) || columns.length === 0) {
    return "Please add at least one column."
  }

  const columnNames = new Set()

  for (const column of columns) {
    const validationError = validateColumn(column)

    if (validationError) {
      return validationError
    }

    const normalizedName = column.name.trim().toLowerCase()

    if (columnNames.has(normalizedName)) {
      return `Duplicate column name found: ${column.name}`
    }

    columnNames.add(normalizedName)
  }

  return ""
}


export function getCaseDistributionTotal(caseDistribution) {
  return Object.values(caseDistribution).reduce(
    (total, value) => total + Number(value || 0),
    0
  )
}


export function isCaseDistributionValid(caseDistribution) {
  return getCaseDistributionTotal(caseDistribution) === 100
}


export function validateDatasetRequest({
  datasetName,
  rowCount,
  columns,
  caseDistribution,
  maximumRowCount = 10000
}) {
  if (!datasetName.trim()) {
    return "Dataset name is required."
  }

  const numericRowCount = Number(rowCount)

  if (
    !numericRowCount ||
    numericRowCount < 1 ||
    numericRowCount > maximumRowCount
  ) {
    return `Row count must be between 1 and ${maximumRowCount.toLocaleString()}.`
  }

  const schemaError = validateSchema(columns)

  if (schemaError) {
    return schemaError
  }

  if (!isCaseDistributionValid(caseDistribution)) {
    return "Case percentages must total exactly 100."
  }

  return ""
}