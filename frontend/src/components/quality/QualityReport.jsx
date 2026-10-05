import {
  formatRuleName,
  getStatusClasses,
  getTotalRowsRepaired
} from "../../utils/formatters"


function MetricCard({
  value,
  label,
  className
}) {
  return (
    <div
      className={`rounded-2xl border px-4 py-4 text-center ${className}`}
    >
      <p className="text-xl font-bold">
        {value ?? 0}
      </p>

      <p className="mt-1 text-xs font-medium">
        {label}
      </p>
    </div>
  )
}


function QualityReport({
  generatedData
}) {
  const report = generatedData?.quality_report
  const summary = generatedData?.summary

  if (!report || !summary) {
    return null
  }

  const checks = Array.isArray(report.checks)
    ? report.checks
    : []

  const qualityScore =
    summary.data_quality_score ??
    report.overall_score ??
    0

  const rulesChecked =
    summary.data_quality_rules_checked ??
    report.rules_checked ??
    checks.length

  const rulesPassed =
    summary.data_quality_rules_passed ??
    report.rules_passed ??
    0

  const rulesFailed =
    summary.data_quality_rules_failed ??
    report.rules_failed ??
    0

  const totalRowsRepaired =
    getTotalRowsRepaired(checks)

  return (
    <section className="mt-6 rounded-3xl border border-emerald-200 bg-white p-6 shadow-xl shadow-emerald-100/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-emerald-600">
            Data quality report
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Generated data quality checks
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            Review the quality rules applied after generation,
            including checked, repaired, and failed rows.
          </p>
        </div>

        <div
          role="status"
          aria-label={`Quality score ${qualityScore}`}
          className="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-3 text-center"
        >
          <p className="text-2xl font-bold text-emerald-700">
            {qualityScore}
          </p>

          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Quality score
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          value={rulesChecked}
          label="Rules checked"
          className="border-slate-200 bg-slate-50 text-slate-950"
        />

        <MetricCard
          value={rulesPassed}
          label="Rules passed"
          className="border-emerald-200 bg-emerald-50 text-emerald-700"
        />

        <MetricCard
          value={rulesFailed}
          label="Rules failed"
          className="border-red-200 bg-red-50 text-red-700"
        />

        <MetricCard
          value={totalRowsRepaired}
          label="Rows repaired"
          className="border-blue-200 bg-blue-50 text-blue-700"
        />
      </div>

      <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 px-4 py-3">
          <p className="text-sm font-bold text-slate-700">
            Quality checks
          </p>

          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600">
            {checks.length}
          </span>
        </div>

        <div className="overflow-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-white">
              <tr>
                <th
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500"
                >
                  Rule
                </th>

                <th
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500"
                >
                  Status
                </th>

                <th
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500"
                >
                  Fields
                </th>

                <th
                  scope="col"
                  className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wide text-slate-500"
                >
                  Checked
                </th>

                <th
                  scope="col"
                  className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wide text-slate-500"
                >
                  Repaired
                </th>

                <th
                  scope="col"
                  className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wide text-slate-500"
                >
                  Failed
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100 bg-white">
              {checks.map((check, index) => {
                const checkKey =
                  check.rule ||
                  `quality-check-${index}`

                const fields =
                  Array.isArray(check.fields_detected) &&
                  check.fields_detected.length > 0
                    ? check.fields_detected.join(", ")
                    : "-"

                return (
                  <tr
                    key={checkKey}
                    className="transition hover:bg-slate-50"
                  >
                    <td className="whitespace-nowrap px-4 py-3 font-semibold text-slate-800">
                      {formatRuleName(check.rule)}
                    </td>

                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wide ${getStatusClasses(
                          check.status
                        )}`}
                      >
                        {check.status || "unknown"}
                      </span>
                    </td>

                    <td
                      className="max-w-sm px-4 py-3 text-slate-600"
                      title={fields}
                    >
                      <span className="block truncate">
                        {fields}
                      </span>
                    </td>

                    <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                      {check.rows_checked ?? 0}
                    </td>

                    <td className="px-4 py-3 text-right tabular-nums font-medium text-blue-700">
                      {check.rows_repaired ?? 0}
                    </td>

                    <td className="px-4 py-3 text-right tabular-nums font-medium text-red-700">
                      {check.failed_rows ?? 0}
                    </td>
                  </tr>
                )
              })}

              {checks.length === 0 && (
                <tr>
                  <td
                    colSpan="6"
                    className="px-4 py-10 text-center text-sm text-slate-500"
                  >
                    No quality-check details are available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}


export default QualityReport