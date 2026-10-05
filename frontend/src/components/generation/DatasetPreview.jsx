import { formatCellValue } from "../../utils/formatters"


function SummaryCard({
  value,
  label,
  tone = "slate"
}) {
  const toneClasses = {
    slate: "border-slate-200 bg-slate-50 text-slate-950",
    blue: "border-blue-200 bg-blue-50 text-blue-700",
    emerald: "border-emerald-200 bg-emerald-50 text-emerald-700",
    amber: "border-amber-200 bg-amber-50 text-amber-700",
    red: "border-red-200 bg-red-50 text-red-700"
  }

  return (
    <div
      className={`rounded-2xl border px-4 py-3 text-center ${
        toneClasses[tone] || toneClasses.slate
      }`}
    >
      <p className="text-lg font-bold tabular-nums">
        {value ?? 0}
      </p>

      <p className="mt-1 text-xs font-medium">
        {label}
      </p>
    </div>
  )
}


function ExportButton({
  children,
  onClick,
  primary = false,
  disabled = false
}) {
  const enabledClasses = primary
    ? "bg-slate-950 text-white shadow-lg shadow-slate-300 hover:bg-slate-800"
    : "border border-slate-300 bg-white text-slate-800 hover:bg-slate-50"

  const disabledClasses =
    "cursor-not-allowed border border-slate-200 bg-slate-100 text-slate-400 shadow-none"

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`rounded-2xl px-5 py-3 text-sm font-semibold transition focus:outline-none focus:ring-4 focus:ring-blue-100 ${
        disabled
          ? disabledClasses
          : enabledClasses
      }`}
    >
      {children}
    </button>
  )
}


function DatasetPreview({
  generatedData,
  isExporting = false,
  onExport
}) {
  if (!generatedData) {
    return null
  }

  const summary = generatedData.summary || {}

  const generatedRows = Array.isArray(
    generatedData.generated_rows
  )
    ? generatedData.generated_rows
    : []

  const previewRows = generatedRows.slice(0, 100)

  const columnNames =
    previewRows.length > 0
      ? Object.keys(previewRows[0])
      : []

  return (
    <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/60">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="text-sm font-semibold text-blue-600">
            Generated dataset
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Preview first 100 rows
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            The backend generated{" "}
            <span className="font-semibold text-slate-800">
              {summary.total_rows ?? generatedRows.length}
            </span>{" "}
            rows. The preview is scrollable horizontally and
            vertically.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <ExportButton
            primary
            disabled={isExporting}
            onClick={() => onExport("csv")}
          >
            Download CSV
          </ExportButton>

          <ExportButton
            disabled={isExporting}
            onClick={() => onExport("json")}
          >
            Download JSON
          </ExportButton>

          <ExportButton
            disabled={isExporting}
            onClick={() => onExport("pipe")}
          >
            Download PSV
          </ExportButton>
        </div>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          value={summary.total_rows ?? generatedRows.length}
          label="Total rows"
          tone="slate"
        />

        <SummaryCard
          value={summary.normal_rows}
          label="Normal rows"
          tone="emerald"
        />

        <SummaryCard
          value={summary.invalid_case_rows}
          label="Invalid rows"
          tone="red"
        />

        <SummaryCard
          value={summary.edge_case_rows}
          label="Edge rows"
          tone="amber"
        />
      </div>

      <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3">
          <div>
            <p className="text-sm font-bold text-slate-700">
              Dataset rows
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Showing {previewRows.length} of{" "}
              {summary.total_rows ?? generatedRows.length} rows
            </p>
          </div>

          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600">
            {columnNames.length} columns
          </span>
        </div>

        {previewRows.length > 0 ? (
          <div className="max-h-[560px] overflow-auto">
            <table className="min-w-max divide-y divide-slate-200 text-sm">
              <thead className="sticky top-0 z-10 bg-slate-50">
                <tr>
                  {columnNames.map((columnName) => (
                    <th
                      key={columnName}
                      scope="col"
                      className="whitespace-nowrap border-r border-slate-200 px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500 last:border-r-0"
                    >
                      {columnName}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100 bg-white">
                {previewRows.map((row, rowIndex) => (
                  <tr
                    key={`preview-row-${rowIndex}`}
                    className="transition hover:bg-blue-50/40"
                  >
                    {columnNames.map((columnName) => {
                      const formattedValue = formatCellValue(
                        row[columnName]
                      )

                      return (
                        <td
                          key={`${rowIndex}-${columnName}`}
                          title={formattedValue}
                          className="max-w-xs truncate whitespace-nowrap border-r border-slate-100 px-4 py-3 text-slate-700 last:border-r-0"
                        >
                          {formattedValue}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-12 text-center">
            <p className="text-sm font-semibold text-slate-700">
              No generated rows are available
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Generate the dataset again or review the request
              configuration.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}


export default DatasetPreview