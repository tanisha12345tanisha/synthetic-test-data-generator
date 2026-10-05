import { API_BASE_URL, getAuthHeaders } from "./apiClient"
import { formatFileName } from "../utils/formatters"



const EXPORT_CONFIG = {
  csv: {
    endpoint: "/export/csv",
    extension: "csv",
    label: "CSV"
  },
  json: {
    endpoint: "/export/json",
    extension: "json",
    label: "JSON"
  },
  pipe: {
    endpoint: "/export/pipe",
    extension: "psv",
    label: "PSV"
  }
}


async function readJsonResponse(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}


function getErrorMessage(data, fallbackMessage) {
  if (typeof data?.detail === "string") {
    return data.detail
  }

  if (typeof data?.message === "string") {
    return data.message
  }

  return fallbackMessage
}


async function postJson(endpoint, requestBody, fallbackMessage) {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      method: "POST",
      headers: getAuthHeaders({
        "Content-Type": "application/json"
      }),
      body: JSON.stringify(requestBody)
    }
  )

  const data = await readJsonResponse(response)

  if (!response.ok) {
    throw new Error(
      getErrorMessage(data, fallbackMessage)
    )
  }

  return data
}


export async function inferSchemaFromCsv(file) {
  if (!file) {
    throw new Error("Please select a CSV file.")
  }

  const formData = new FormData()
  formData.append("file", file)

  const response = await fetch(
    `${API_BASE_URL}/infer-schema`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData
    }
  )

  const data = await readJsonResponse(response)

  if (!response.ok) {
    throw new Error(
      getErrorMessage(
        data,
        "Failed to infer schema from CSV."
      )
    )
  }

  return data
}


export function generateDataset(schemaRequest) {
  return postJson(
    "/generate",
    schemaRequest,
    "Failed to generate dataset."
  )
}


export async function exportDataset({
  format,
  schemaRequest,
  datasetName
}) {
  const exportConfig = EXPORT_CONFIG[format]

  if (!exportConfig) {
    throw new Error("Unsupported export format.")
  }

  const response = await fetch(
    `${API_BASE_URL}${exportConfig.endpoint}`,
    {
      method: "POST",
      headers: getAuthHeaders({
        "Content-Type": "application/json"
      }),
      body: JSON.stringify(schemaRequest)
    }
  )

  if (!response.ok) {
    const data = await readJsonResponse(response)

    throw new Error(
      getErrorMessage(
        data,
        `Failed to export ${exportConfig.label} file.`
      )
    )
  }

  const blob = await response.blob()
  const fileUrl = window.URL.createObjectURL(blob)
  const safeDatasetName = formatFileName(datasetName)

  try {
    const link = document.createElement("a")

    link.href = fileUrl
    link.download =
      `${safeDatasetName}.${exportConfig.extension}`

    document.body.appendChild(link)
    link.click()
    link.remove()
  } finally {
    window.URL.revokeObjectURL(fileUrl)
  }
}


export function getApiBaseUrl() {
  return API_BASE_URL
}