import { CASE_PERCENTAGE_FIELDS } from "../../constants/caseTypes"


function CaseConfiguration({
  caseDistribution,
  caseDistributionTotal,
  isDistributionValid,
  isGenerating,
  errorMessage,
  successMessage,
  onDistributionChange,
  onGenerate
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-blue-600">
            Case configuration
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Configure test coverage percentages
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            Control how normal, edge, invalid, duplicate, null, and
            violation rows are distributed in the generated dataset.
          </p>
        </div>

        <div
          role="status"
          aria-live="polite"
          className={`rounded-2xl border px-4 py-3 text-sm font-bold ${
            isDistributionValid
              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
              : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          Total: {caseDistributionTotal}%
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {CASE_PERCENTAGE_FIELDS.map((field) => {
          const inputId = `case-percentage-${field.key}`

          return (
            <div
              key={field.key}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-4 transition focus-within:border-blue-300 focus-within:bg-blue-50/40"
            >
              <div className="flex items-center justify-between gap-4">
                <label
                  htmlFor={inputId}
                  className="min-w-0 flex-1 cursor-pointer"
                >
                  <span className="text-sm font-semibold text-slate-900">
                    {field.label}
                  </span>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {field.description}
                  </p>
                </label>

                <div className="relative shrink-0">
                  <input
                    id={inputId}
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value={caseDistribution[field.key]}
                    onChange={(event) =>
                      onDistributionChange(
                        field.key,
                        event.target.value
                      )
                    }
                    aria-label={`${field.label} percentage`}
                    className="w-24 rounded-xl border border-slate-200 bg-white px-3 py-2 pr-8 text-right text-sm font-semibold text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />

                  <span
                    aria-hidden="true"
                    className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-slate-400"
                  >
                    %
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {!isDistributionValid && (
        <div
          role="alert"
          className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
        >
          Case percentages must total exactly 100 before generating
          data.
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-200 bg-slate-50 p-5">
        <div>
          <h3 className="text-lg font-bold text-slate-950">
            Ready to generate?
          </h3>

          <p className="mt-1 text-sm text-slate-600">
            Generate synthetic rows using the current schema and case
            configuration.
          </p>
        </div>

        <button
          type="button"
          onClick={onGenerate}
          disabled={!isDistributionValid || isGenerating}
          aria-busy={isGenerating}
          className={`rounded-2xl px-6 py-3 text-sm font-semibold text-white shadow-lg transition focus:outline-none focus:ring-4 focus:ring-blue-100 ${
            !isDistributionValid || isGenerating
              ? "cursor-not-allowed bg-slate-400 shadow-none"
              : "bg-blue-600 shadow-blue-200 hover:bg-blue-700"
          }`}
        >
          {isGenerating
            ? "Generating..."
            : "Generate Dataset"}
        </button>
      </div>

      {(errorMessage || successMessage) && (
        <div className="mt-5">
          {errorMessage && (
            <div
              role="alert"
              className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
            >
              {errorMessage}
            </div>
          )}

          {!errorMessage && successMessage && (
            <div
              role="status"
              aria-live="polite"
              className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700"
            >
              {successMessage}
            </div>
          )}
        </div>
      )}
    </section>
  )
}


export default CaseConfiguration