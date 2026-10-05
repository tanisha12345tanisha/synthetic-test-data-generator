export function formatRuleName(ruleName) {
  return String(ruleName || "")
    .split("_")
    .filter(Boolean)
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1)
    )
    .join(" ")
}


export function getStatusClasses(status) {
  const normalizedStatus = String(status || "")
    .trim()
    .toLowerCase()

  if (normalizedStatus === "pass") {
    return "bg-emerald-100 text-emerald-700"
  }

  if (normalizedStatus === "fail") {
    return "bg-red-100 text-red-700"
  }

  return "bg-slate-200 text-slate-700"
}


export function formatCellValue(value) {
  if (value === null) {
    return "null"
  }

  if (value === undefined) {
    return ""
  }

  if (typeof value === "object") {
    return JSON.stringify(value)
  }

  return String(value)
}


export function getTotalRowsRepaired(checks) {
  if (!Array.isArray(checks)) {
    return 0
  }

  return checks.reduce(
    (total, check) =>
      total + Number(check?.rows_repaired || 0),
    0
  )
}


export function formatFileName(datasetName, fallback = "synthetic_dataset") {
  const normalizedName = String(datasetName || "")
    .trim()
    .replace(/[^a-zA-Z0-9_-]+/g, "_")
    .replace(/^_+|_+$/g, "")

  return normalizedName || fallback
}