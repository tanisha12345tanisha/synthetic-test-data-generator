import { useState } from "react"

const API_BASE_URL = "http://127.0.0.1:8000"

const DATA_TYPES = [
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
]

const CASE_PERCENTAGE_FIELDS = [
  { key: "normal", label: "Normal", description: "Valid standard rows" },
  { key: "edge_case", label: "Edge case", description: "Extreme but useful test values" },
  { key: "corner_case", label: "Corner case", description: "Special boundary-like data" },
  { key: "boundary_case", label: "Boundary case", description: "Min/max and boundary values" },
  { key: "invalid_case", label: "Invalid case", description: "Clearly invalid values" },
  { key: "duplicate_case", label: "Duplicate case", description: "Duplicate unique fields" },
  { key: "null_case", label: "Null case", description: "Null values for testing" },
  { key: "format_violation_case", label: "Format violation", description: "Invalid email, phone, date, etc." },
  { key: "range_violation_case", label: "Range violation", description: "Values below min or above max" },
  { key: "length_violation_case", label: "Length violation", description: "Text below/above allowed length" }
]

const NUMERIC_TYPES = ["integer", "number", "decimal", "float", "currency_amount"]
const LENGTH_TYPES = ["string", "long_text", "name", "first_name", "last_name", "address", "company", "job_title"]
const DATE_TIME_TYPES = ["date", "datetime", "timestamp"]
const BOOLEAN_TYPES = ["boolean"]

function supportsNumericRange(type) {
  return NUMERIC_TYPES.includes(type)
}

function supportsLengthRange(type) {
  return LENGTH_TYPES.includes(type)
}

function supportsCategoryValues(type) {
  return type === "category"
}

function supportsPrefix(type) {
  return type === "id"
}

function supportsPattern(type) {
  return type === "regex"
}

function supportsDateRange(type) {
  return DATE_TIME_TYPES.includes(type)
}

function supportsBooleanProbability(type) {
  return BOOLEAN_TYPES.includes(type)
}

function hasAdvancedFields(type) {
  return (
    supportsNumericRange(type) ||
    supportsLengthRange(type) ||
    supportsCategoryValues(type) ||
    supportsPrefix(type) ||
    supportsPattern(type) ||
    supportsDateRange(type) ||
    supportsBooleanProbability(type)
  )
}

function createEmptyColumn() {
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

function App() {
  const [datasetName, setDatasetName] = useState("")
  const [rowCount, setRowCount] = useState("")
  const [columns, setColumns] = useState([])

  const [caseDistribution, setCaseDistribution] = useState({
    normal: 70,
    edge_case: 10,
    corner_case: 5,
    boundary_case: 5,
    invalid_case: 5,
    duplicate_case: 1,
    null_case: 1,
    format_violation_case: 1,
    range_violation_case: 1,
    length_violation_case: 1
  })

  const [generatedData, setGeneratedData] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [successMessage, setSuccessMessage] = useState("")
  const [isInferringSchema, setIsInferringSchema] = useState(false)
  const [activeModal, setActiveModal] = useState(null)
  const [isSchemaReady, setIsSchemaReady] = useState(false)

  function openUploadModal() {
    setErrorMessage("")
    setSuccessMessage("")
    setActiveModal("upload")
  }

  function openManualSchemaModal() {
    setErrorMessage("")
    setSuccessMessage("")
    setActiveModal("manual")
  }

  function closeModal() {
    setActiveModal(null)
  }

  function addColumn() {
    setColumns((previousColumns) => [...previousColumns, createEmptyColumn()])
  }

  function updateColumn(columnId, field, value) {
    setColumns((previousColumns) =>
      previousColumns.map((column) =>
        column.id === columnId
          ? {
              ...column,
              [field]: value
            }
          : column
      )
    )
  }

  function toggleColumnBoolean(columnId, field) {
    setColumns((previousColumns) =>
      previousColumns.map((column) => {
        if (column.id !== columnId) {
          return column
        }

        const nextValue = !column[field]

        if (field === "required") {
          return {
            ...column,
            required: nextValue,
            nullable: nextValue ? false : column.nullable
          }
        }

        if (field === "nullable") {
          return {
            ...column,
            nullable: nextValue,
            required: nextValue ? false : column.required
          }
        }

        return {
          ...column,
          [field]: nextValue
        }
      })
    )
  }

  function deleteColumn(columnId) {
    setColumns((previousColumns) =>
      previousColumns.filter((column) => column.id !== columnId)
    )
  }

  function updateCaseDistribution(field, value) {
    const numericValue = Number(value)

    setCaseDistribution((previousDistribution) => ({
      ...previousDistribution,
      [field]: Number.isNaN(numericValue) ? 0 : numericValue
    }))
  }

  function parseWeights(weightsText) {
    const weights = {}

    weightsText
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
      .forEach((item) => {
        const [key, value] = item.split(":").map((part) => part.trim())

        if (key && value !== undefined && value !== "") {
          weights[key] = Number(value)
        }
      })

    return weights
  }

  function convertInferredColumnsToFrontendColumns(inferredColumns) {
    const reservedColumns = [
      "__case_type",
      "__case_labels",
      "__case_reasons"
    ]

    return inferredColumns
      .filter((column) => !reservedColumns.includes(column.name))
      .map((column) => ({
        id: crypto.randomUUID(),
        name: column.name || "",
        type: column.type || "string",
        required: Boolean(column.required),
        nullable: Boolean(column.nullable),
        unique: Boolean(column.unique),
        min: column.min !== null && column.min !== undefined ? String(column.min) : "",
        max: column.max !== null && column.max !== undefined ? String(column.max) : "",
        min_length: column.min_length !== null && column.min_length !== undefined ? String(column.min_length) : "",
        max_length: column.max_length !== null && column.max_length !== undefined ? String(column.max_length) : "",
        values: Array.isArray(column.values) ? column.values.join(",") : "",
        prefix: column.prefix || "",
        pattern: column.pattern || "",
        distribution_type: column.distribution?.type || "",
        mean: column.distribution?.mean !== null && column.distribution?.mean !== undefined ? String(column.distribution.mean) : "",
        std: column.distribution?.std !== null && column.distribution?.std !== undefined ? String(column.distribution.std) : "",
        true_probability:
          column.distribution?.true_probability !== null && column.distribution?.true_probability !== undefined
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

  async function handleSchemaInference(event) {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    setIsInferringSchema(true)
    setErrorMessage("")
    setSuccessMessage("")
    setGeneratedData(null)

    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch(`${API_BASE_URL}/infer-schema`, {
        method: "POST",
        body: formData
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Failed to infer schema from CSV."
        )
      }

      const inferredColumns = convertInferredColumnsToFrontendColumns(data.columns)
      setColumns(inferredColumns)
      setIsSchemaReady(true)
      closeModal()
      setSuccessMessage(data.message || "Schema inferred successfully from CSV.")
    } catch (error) {
      setErrorMessage(error.message)
    } finally {
      setIsInferringSchema(false)
      event.target.value = ""
    }
  }

  function buildSchemaPreview() {
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

        if (supportsCategoryValues(column.type) && column.values.trim() !== "") {
          schemaColumn.values = column.values
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean)
        }

        if (supportsPrefix(column.type) && column.prefix.trim() !== "") {
          schemaColumn.prefix = column.prefix.trim()
        }

        if (supportsPattern(column.type) && column.pattern.trim() !== "") {
          schemaColumn.pattern = column.pattern.trim()
        }

        if (supportsNumericRange(column.type) && column.distribution_type) {
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

        if (supportsBooleanProbability(column.type) && column.true_probability !== "") {
          schemaColumn.distribution = {
            type: "boolean_probability",
            true_probability: Number(column.true_probability)
          }
        }

        if (supportsDateRange(column.type) && column.start_date && column.end_date) {
          schemaColumn.distribution = {
            type: "date_range",
            start_date: column.start_date,
            end_date: column.end_date
          }
        }

        if (supportsCategoryValues(column.type) && column.weights.trim() !== "") {
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

  const caseDistributionTotal = Object.values(caseDistribution).reduce(
    (total, value) => total + Number(value || 0),
    0
  )

  const isCaseDistributionValid = caseDistributionTotal === 100
  const schemaPreview = buildSchemaPreview()

  function validateSchemaOnly() {
    if (columns.length === 0) {
      return "Please add at least one column."
    }

    const columnNames = new Set()

    for (const column of columns) {
      if (!column.name.trim()) {
        return "Every column must have a name."
      }

      if (!column.type.trim()) {
        return `Please select a data type for column "${column.name || "Unnamed column"}".`
      }

      const normalizedName = column.name.trim().toLowerCase()

      if (columnNames.has(normalizedName)) {
        return `Duplicate column name found: ${column.name}`
      }

      columnNames.add(normalizedName)

      if (["__case_type", "__case_labels", "__case_reasons"].includes(column.name.trim())) {
        return `${column.name} is reserved for system metadata.`
      }

      if (column.type === "id" && !column.prefix.trim()) {
        return `ID column "${column.name}" must have a prefix.`
      }

      if (column.type === "category" && !column.values.trim()) {
        return `Category column "${column.name}" must have comma-separated values.`
      }

      if (column.type === "regex" && !column.pattern.trim()) {
        return `Regex column "${column.name}" must have a pattern.`
      }

      if (column.min !== "" && column.max !== "") {
        const minValue = Number(column.min)
        const maxValue = Number(column.max)

        if (minValue > maxValue) {
          return `Column "${column.name}" has min greater than max.`
        }
      }

      if (column.min_length !== "" && column.max_length !== "") {
        const minLength = Number(column.min_length)
        const maxLength = Number(column.max_length)

        if (minLength > maxLength) {
          return `Column "${column.name}" has min length greater than max length.`
        }
      }

      if (supportsBooleanProbability(column.type) && column.true_probability !== "") {
        const probability = Number(column.true_probability)

        if (Number.isNaN(probability) || probability < 0 || probability > 100) {
          return `True probability for column "${column.name}" must be between 0 and 100.`
        }
      }

      if (supportsDateRange(column.type)) {
        if ((column.start_date && !column.end_date) || (!column.start_date && column.end_date)) {
          return `Date range for column "${column.name}" requires both start date and end date.`
        }

        if (column.start_date && column.end_date && column.start_date > column.end_date) {
          return `Start date cannot be after end date for column "${column.name}".`
        }
      }

      if (supportsCategoryValues(column.type) && column.weights.trim() !== "") {
        const parsedWeights = parseWeights(column.weights)

        if (Object.keys(parsedWeights).length === 0) {
          return `Weights for category column "${column.name}" must use format value:weight.`
        }

        const hasInvalidWeight = Object.values(parsedWeights).some((value) => Number.isNaN(Number(value)))

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
        const missingWeights = categoryValues.filter((value) => !weightKeys.includes(value))

        if (missingWeights.length > 0) {
          return `Weights missing for category values: ${missingWeights.join(", ")}.`
        }
      }

      if (column.distribution_type === "normal" && column.std !== "") {
        if (Number(column.std) <= 0) {
          return `Standard deviation for column "${column.name}" must be greater than 0.`
        }
      }
    }

    return ""
  }

  function validateFrontendRequest() {
    if (!datasetName.trim()) {
      return "Dataset name is required."
    }

    const numericRowCount = Number(rowCount)

    if (!numericRowCount || numericRowCount < 1 || numericRowCount > 10000) {
      return "Row count must be between 1 and 10,000."
    }

    const schemaError = validateSchemaOnly()

    if (schemaError) {
      return schemaError
    }

    if (!isCaseDistributionValid) {
      return "Case percentages must total exactly 100."
    }

    return ""
  }

  function handleCreateSchema() {
    const schemaError = validateSchemaOnly()

    if (schemaError) {
      setErrorMessage(schemaError)
      return
    }

    setGeneratedData(null)
    setIsSchemaReady(true)
    closeModal()
    setErrorMessage("")
    setSuccessMessage("Schema created successfully. Configure cases and generate your dataset.")
  }

  async function handleGenerateDataset() {
    const validationError = validateFrontendRequest()

    if (validationError) {
      setErrorMessage(validationError)
      return
    }

    setIsGenerating(true)
    setErrorMessage("")
    setSuccessMessage("")
    setGeneratedData(null)

    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(schemaPreview)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Failed to generate dataset."
        )
      }

      setGeneratedData(data)
      setSuccessMessage("Dataset generated successfully.")
    } catch (error) {
      setErrorMessage(error.message)
    } finally {
      setIsGenerating(false)
    }
  }

  async function handleExport(format) {
    const validationError = validateFrontendRequest()

    if (validationError) {
      setErrorMessage(validationError)
      return
    }

    setErrorMessage("")

    try {
      const endpointMap = {
        csv: `${API_BASE_URL}/export/csv`,
        json: `${API_BASE_URL}/export/json`,
        pipe: `${API_BASE_URL}/export/pipe`
      }

      const extensionMap = {
        csv: "csv",
        json: "json",
        pipe: "psv"
      }

      const endpoint = endpointMap[format]
      const fileExtension = extensionMap[format]

      if (!endpoint || !fileExtension) {
        throw new Error("Unsupported export format.")
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(schemaPreview)
      })

      if (!response.ok) {
        let detailMessage = `Failed to export ${format.toUpperCase()} file.`

        try {
          const errorData = await response.json()
          if (typeof errorData.detail === "string") {
            detailMessage = errorData.detail
          }
        } catch {
          detailMessage = `Failed to export ${format.toUpperCase()} file.`
        }

        throw new Error(detailMessage)
      }

      const blob = await response.blob()
      const fileUrl = window.URL.createObjectURL(blob)

      const link = document.createElement("a")
      link.href = fileUrl
      link.download = `${datasetName || "synthetic_dataset"}.${fileExtension}`
      document.body.appendChild(link)
      link.click()
      link.remove()

      window.URL.revokeObjectURL(fileUrl)
    } catch (error) {
      setErrorMessage(error.message)
    }
  }

  function renderMessage() {
    if (errorMessage) {
      return (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {errorMessage}
        </div>
      )
    }

    if (successMessage) {
      return (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
          {successMessage}
        </div>
      )
    }

    return null
  }

  function renderColumnEditor() {
    return (
      <div className="space-y-4">
        {columns.length === 0 && (
          <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
            <p className="text-sm font-medium text-slate-600">
              No columns added yet.
            </p>
            <button
              type="button"
              onClick={addColumn}
              className="mt-4 rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700"
            >
              + Add First Column
            </button>
          </div>
        )}

        {columns.length > 0 && (
          <>
            <div className="flex justify-end">
              <button
                type="button"
                onClick={addColumn}
                className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700"
              >
                + Add Column
              </button>
            </div>

            {columns.map((column, index) => (
              <div
                key={column.id}
                className="rounded-3xl border border-slate-200 bg-slate-50 p-5"
              >
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-900">
                    Column {index + 1}
                  </h3>
                  <button
                    type="button"
                    onClick={() => deleteColumn(column.id)}
                    className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-100"
                  >
                    Delete
                  </button>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Column name
                    </span>
                    <input
                      value={column.name}
                      onChange={(event) =>
                        updateColumn(column.id, "name", event.target.value)
                      }
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    />
                  </label>

                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Data type
                    </span>
                    <select
                      value={column.type}
                      onChange={(event) =>
                        updateColumn(column.id, "type", event.target.value)
                      }
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    >
                      <option value="" disabled>
                        Select data type
                      </option>
                      {DATA_TYPES.map((dataType) => (
                        <option key={dataType} value={dataType}>
                          {dataType}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="grid grid-cols-3 gap-2 pt-7">
                    {[
                      ["required", "Required"],
                      ["nullable", "Nullable"],
                      ["unique", "Unique"]
                    ].map(([field, label]) => (
                      <button
                        key={field}
                        type="button"
                        onClick={() => toggleColumnBoolean(column.id, field)}
                        className={`rounded-xl px-3 py-2 text-xs font-semibold transition ${
                          column[field]
                            ? "bg-blue-600 text-white"
                            : "border border-slate-200 bg-white text-slate-600"
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                {column.type && hasAdvancedFields(column.type) && (
                  <div className="mt-4 space-y-4 rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                      Type-specific configuration
                    </p>

                    {supportsNumericRange(column.type) && (
                      <div className="grid gap-4 md:grid-cols-3">
                        <input
                          value={column.min}
                          onChange={(event) =>
                            updateColumn(column.id, "min", event.target.value)
                          }
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                          placeholder="Min value"
                        />

                        <input
                          value={column.max}
                          onChange={(event) =>
                            updateColumn(column.id, "max", event.target.value)
                          }
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                          placeholder="Max value"
                        />

                        <select
                          value={column.distribution_type}
                          onChange={(event) =>
                            updateColumn(column.id, "distribution_type", event.target.value)
                          }
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                        >
                          <option value="">No distribution</option>
                          <option value="uniform">Uniform</option>
                          <option value="normal">Normal</option>
                          <option value="exponential">Exponential</option>
                        </select>

                        {column.distribution_type === "normal" && (
                          <>
                            <input
                              value={column.mean}
                              onChange={(event) =>
                                updateColumn(column.id, "mean", event.target.value)
                              }
                              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                              placeholder="Mean"
                            />
                            <input
                              value={column.std}
                              onChange={(event) =>
                                updateColumn(column.id, "std", event.target.value)
                              }
                              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                              placeholder="Std deviation"
                            />
                          </>
                        )}

                        {column.distribution_type === "exponential" && (
                          <input
                            value={column.mean}
                            onChange={(event) =>
                              updateColumn(column.id, "mean", event.target.value)
                            }
                            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                            placeholder="Mean / scale"
                          />
                        )}
                      </div>
                    )}

                    {supportsLengthRange(column.type) && (
                      <div className="grid gap-4 md:grid-cols-2">
                        <input
                          value={column.min_length}
                          onChange={(event) =>
                            updateColumn(column.id, "min_length", event.target.value)
                          }
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                          placeholder="Min length"
                        />
                        <input
                          value={column.max_length}
                          onChange={(event) =>
                            updateColumn(column.id, "max_length", event.target.value)
                          }
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                          placeholder="Max length"
                        />
                      </div>
                    )}

                    {supportsBooleanProbability(column.type) && (
                      <input
                        value={column.true_probability}
                        onChange={(event) =>
                          updateColumn(column.id, "true_probability", event.target.value)
                        }
                        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                        placeholder="True probability % e.g. 80"
                      />
                    )}

                    {supportsDateRange(column.type) && (
                      <div className="grid gap-4 md:grid-cols-2">
                        <input
                          type="date"
                          value={column.start_date}
                          onChange={(event) =>
                            updateColumn(column.id, "start_date", event.target.value)
                          }
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                        />
                        <input
                          type="date"
                          value={column.end_date}
                          onChange={(event) =>
                            updateColumn(column.id, "end_date", event.target.value)
                          }
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                        />
                      </div>
                    )}

                    {supportsCategoryValues(column.type) && (
                      <div className="grid gap-4 md:grid-cols-2">
                        <input
                          value={column.values}
                          onChange={(event) =>
                            updateColumn(column.id, "values", event.target.value)
                          }
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                          placeholder="Values: Pune,Mumbai,Bengaluru"
                        />
                        <input
                          value={column.weights}
                          onChange={(event) =>
                            updateColumn(column.id, "weights", event.target.value)
                          }
                          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                          placeholder="Weights: Pune:70,Mumbai:30"
                        />
                      </div>
                    )}

                    {supportsPrefix(column.type) && (
                      <input
                        value={column.prefix}
                        onChange={(event) =>
                          updateColumn(column.id, "prefix", event.target.value)
                        }
                        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                        placeholder="Prefix e.g. CUST"
                      />
                    )}

                    {supportsPattern(column.type) && (
                      <input
                        value={column.pattern}
                        onChange={(event) =>
                          updateColumn(column.id, "pattern", event.target.value)
                        }
                        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                        placeholder="Regex pattern"
                      />
                    )}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <h1 className="text-2xl font-bold">Synthetic Test Data Generator</h1>
        </div>
      </header>

      {!isSchemaReady && (
        <section className="mx-auto max-w-6xl px-6 py-12">
          <div className="mb-8 text-center">
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">
              Start generating test data
            </p>
            <h2 className="mt-3 text-4xl font-bold tracking-tight text-slate-950">
              Choose how to create your schema
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-slate-600">
              Upload a CSV to infer schema automatically or create a custom schema manually. Generated output remains synthetic-only.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <button
              type="button"
              onClick={openUploadModal}
              className="group rounded-3xl border border-slate-200 bg-white p-8 text-left shadow-xl shadow-slate-200/60 transition hover:-translate-y-1 hover:border-blue-300 hover:shadow-2xl"
            >
              <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-xl font-bold text-blue-700">
                CSV
              </div>
              <h3 className="text-2xl font-bold text-slate-950">Upload CSV</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                Infer column names, data types, ranges, categories, and date ranges from a sample CSV.
              </p>
              <div className="mt-6 text-sm font-semibold text-blue-600 group-hover:text-blue-700">
                Upload and infer schema
              </div>
            </button>

            <button
              type="button"
              onClick={openManualSchemaModal}
              className="group rounded-3xl border border-slate-200 bg-white p-8 text-left shadow-xl shadow-slate-200/60 transition hover:-translate-y-1 hover:border-blue-300 hover:shadow-2xl"
            >
              <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-xl font-bold text-emerald-700">
                NEW
              </div>
              <h3 className="text-2xl font-bold text-slate-950">Create Schema</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                Build a fully custom schema by adding columns, choosing data types, and setting constraints.
              </p>
              <div className="mt-6 text-sm font-semibold text-blue-600 group-hover:text-blue-700">
                Build schema manually
              </div>
            </button>
          </div>
        </section>
      )}

      {isSchemaReady && (
        <section className="mx-auto max-w-7xl px-6 py-8">
          <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/60">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-blue-600">Dataset setup</p>
                  <h2 className="mt-2 text-2xl font-bold">Review schema before case configuration</h2>
                  <p className="mt-2 text-sm text-slate-600">
                    Schema is visible first. You can edit it any time before generation.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={openManualSchemaModal}
                  className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
                >
                  Edit Schema
                </button>
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Dataset name</span>
                  <input
                    value={datasetName}
                    onChange={(event) => setDatasetName(event.target.value)}
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Row count</span>
                  <input
                    type="number"
                    min="1"
                    max="10000"
                    value={rowCount}
                    onChange={(event) => setRowCount(event.target.value)}
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />
                  <p className="mt-1 text-xs text-slate-500">Maximum allowed: 10,000 rows</p>
                </label>
              </div>

              <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200">
                <div className="bg-slate-50 px-4 py-3 text-sm font-bold text-slate-700">
                  Schema columns ({columns.length})
                </div>
                <div className="max-h-80 overflow-auto">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="sticky top-0 bg-white">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">Name</th>
                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">Type</th>
                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">Required</th>
                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">Nullable</th>
                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">Unique</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {columns.map((column) => (
                        <tr key={column.id}>
                          <td className="px-4 py-3 font-medium text-slate-800">{column.name}</td>
                          <td className="px-4 py-3 text-slate-600">{column.type}</td>
                          <td className="px-4 py-3 text-slate-600">{column.required ? "Yes" : "No"}</td>
                          <td className="px-4 py-3 text-slate-600">{column.nullable ? "Yes" : "No"}</td>
                          <td className="px-4 py-3 text-slate-600">{column.unique ? "Yes" : "No"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <details className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <summary className="cursor-pointer text-sm font-semibold text-slate-700">View request JSON</summary>
                <pre className="mt-4 max-h-96 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                  {JSON.stringify(schemaPreview, null, 2)}
                </pre>
              </details>
            </section>

            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/60">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-blue-600">Case configuration</p>
                  <h2 className="mt-2 text-2xl font-bold text-slate-950">Configure test coverage percentages</h2>
                  <p className="mt-2 text-sm text-slate-600">
                    These percentages control how normal, edge, invalid, duplicate, null, and violation rows are mixed into the dataset.
                  </p>
                </div>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm font-bold ${
                    isCaseDistributionValid
                      ? "border border-emerald-200 bg-emerald-50 text-emerald-700"
                      : "border border-red-200 bg-red-50 text-red-700"
                  }`}
                >
                  Total: {caseDistributionTotal}%
                </div>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                {CASE_PERCENTAGE_FIELDS.map((field) => (
                  <label key={field.key} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <span className="text-sm font-semibold text-slate-900">{field.label}</span>
                        <p className="mt-1 text-xs text-slate-500">{field.description}</p>
                      </div>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={caseDistribution[field.key]}
                        onChange={(event) => updateCaseDistribution(field.key, event.target.value)}
                        className="w-24 rounded-xl border border-slate-200 bg-white px-3 py-2 text-right text-sm font-semibold outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                      />
                    </div>
                  </label>
                ))}
              </div>

              {!isCaseDistributionValid && (
                <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                  Case percentages must total exactly 100 before generating data.
                </div>
              )}

              <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-200 bg-slate-50 p-5">
                <div>
                  <h3 className="text-lg font-bold text-slate-950">Ready to generate?</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    Generate synthetic rows using the current schema and case configuration.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleGenerateDataset}
                  disabled={!isCaseDistributionValid || isGenerating}
                  className={`rounded-2xl px-6 py-3 text-sm font-semibold text-white shadow-lg transition ${
                    !isCaseDistributionValid || isGenerating
                      ? "cursor-not-allowed bg-slate-400 shadow-none"
                      : "bg-blue-600 shadow-blue-200 hover:bg-blue-700"
                  }`}
                >
                  {isGenerating ? "Generating..." : "Generate Dataset"}
                </button>
              </div>

              <div className="mt-5">{renderMessage()}</div>
            </section>
          </div>

          {generatedData && (
            <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/60">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-blue-600">Generated dataset</p>
                  <h2 className="mt-2 text-2xl font-bold text-slate-950">Preview first 100 rows</h2>
                  <p className="mt-2 text-sm text-slate-600">
                    Backend generated {generatedData.summary.total_rows} rows. Preview is scrollable horizontally and vertically.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <div className="rounded-2xl bg-slate-50 px-4 py-3 text-center">
                    <p className="text-lg font-bold">{generatedData.summary.total_rows}</p>
                    <p className="text-xs text-slate-500">Rows</p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 px-4 py-3 text-center">
                    <p className="text-lg font-bold">{generatedData.summary.normal_rows}</p>
                    <p className="text-xs text-slate-500">Normal</p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 px-4 py-3 text-center">
                    <p className="text-lg font-bold">{generatedData.summary.invalid_case_rows}</p>
                    <p className="text-xs text-slate-500">Invalid</p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 px-4 py-3 text-center">
                    <p className="text-lg font-bold">{generatedData.summary.edge_case_rows}</p>
                    <p className="text-xs text-slate-500">Edge</p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => handleExport("csv")}
                    className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-slate-300 transition hover:bg-slate-800"
                  >
                    Download CSV
                  </button>
                  <button
                    type="button"
                    onClick={() => handleExport("json")}
                    className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
                  >
                    Download JSON
                  </button>
                  <button
                    type="button"
                    onClick={() => handleExport("pipe")}
                    className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
                  >
                    Download Pipe
                  </button>
                </div>
              </div>

              <div className="mt-6 max-h-[560px] overflow-auto rounded-2xl border border-slate-200">
                <table className="min-w-max divide-y divide-slate-200 text-sm">
                  <thead className="sticky top-0 bg-slate-50">
                    <tr>
                      {Object.keys(generatedData.generated_rows[0] || {}).map((columnName) => (
                        <th key={columnName} className="whitespace-nowrap px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">
                          {columnName}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {generatedData.generated_rows.slice(0, 100).map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-slate-50">
                        {Object.entries(row).map(([key, value]) => (
                          <td
                            key={key}
                            className="max-w-xs truncate whitespace-nowrap px-4 py-3 text-slate-700"
                            title={typeof value === "object" ? JSON.stringify(value) : String(value)}
                          >
                            {typeof value === "object" ? JSON.stringify(value) : String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </section>
      )}

      {activeModal === "upload" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
          <div className="w-full max-w-xl rounded-3xl bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-blue-600">Upload CSV</p>
                <h3 className="mt-2 text-2xl font-bold text-slate-950">Infer schema from CSV</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  The CSV is used only for schema inference. Uploaded values are not copied into generated output.
                </p>
              </div>
              <button type="button" onClick={closeModal} className="rounded-full bg-slate-100 px-3 py-1 text-sm font-bold text-slate-600 hover:bg-slate-200">
                ×
              </button>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Dataset name</span>
                <input
                  value={datasetName}
                  onChange={(event) => setDatasetName(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Row count</span>
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={rowCount}
                  onChange={(event) => setRowCount(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>
            </div>

            <label className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-blue-200 bg-blue-50/60 px-6 py-10 text-center transition hover:border-blue-400">
              <span className="text-sm font-semibold text-blue-700">
                {isInferringSchema ? "Inferring schema..." : "Choose CSV file"}
              </span>
              <span className="mt-1 text-xs text-slate-500">Only .csv files are supported</span>
              <input
                type="file"
                accept=".csv"
                onChange={handleSchemaInference}
                disabled={isInferringSchema}
                className="hidden"
              />
            </label>
          </div>
        </div>
      )}

      {activeModal === "manual" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
          <div className="max-h-[90vh] w-full max-w-6xl overflow-auto rounded-3xl bg-white p-6 shadow-2xl">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-blue-600">Create Schema</p>
                <h3 className="mt-2 text-2xl font-bold text-slate-950">Build schema manually</h3>
                <p className="mt-2 text-sm text-slate-600">Add columns, choose data types, and click Create Schema.</p>
              </div>
              <button type="button" onClick={closeModal} className="rounded-full bg-slate-100 px-3 py-1 text-sm font-bold text-slate-600 hover:bg-slate-200">
                ×
              </button>
            </div>

            <div className="mb-6 grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Dataset name</span>
                <input
                  value={datasetName}
                  onChange={(event) => setDatasetName(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Row count</span>
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={rowCount}
                  onChange={(event) => setRowCount(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>
            </div>

            {renderColumnEditor()}

            <div className="mt-6 flex justify-end gap-3 border-t border-slate-200 pt-5">
              <button
                type="button"
                onClick={closeModal}
                className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreateSchema}
                className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                Create Schema
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

export default App
