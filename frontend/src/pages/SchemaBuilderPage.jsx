import BuilderProgress from "../components/schema/BuilderProgress"
import ColumnEditor from "../components/schema/ColumnEditor"


function SchemaBuilderPage({
  sourceType = "manual",
  datasetName,
  rowCount,
  columns,
  errorMessage,
  maximumRowCount = 10000,
  onDatasetNameChange,
  onRowCountChange,
  onAddColumn,
  onUpdateColumn,
  onToggleColumnBoolean,
  onDeleteColumn,
  onBack,
  onContinue
}) {
  const isCsvSource = sourceType === "csv"

  return (
    <section className="min-h-[calc(100vh-73px)] bg-slate-50">
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <div className="flex items-start gap-4">
            <button
              type="button"
              onClick={onBack}
              aria-label="Return to schema source selection"
              className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-lg text-slate-600 transition hover:bg-slate-50 hover:text-slate-950 focus:outline-none focus:ring-4 focus:ring-blue-100"
            >
              ←
            </button>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-bold text-slate-950">
                  Create dataset
                </h1>

                <span
                  className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                    isCsvSource
                      ? "border-blue-200 bg-blue-50 text-blue-700"
                      : "border-emerald-200 bg-emerald-50 text-emerald-700"
                  }`}
                >
                  {isCsvSource
                    ? "CSV inferred"
                    : "Manual schema"}
                </span>
              </div>

              <p className="mt-1 text-sm text-slate-500">
                Define the dataset details and configure its schema.
              </p>
            </div>
          </div>

          <div className="hidden items-center gap-2 text-xs text-slate-500 sm:flex">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />

            Synthetic-only generation
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-6 py-6">
        <BuilderProgress
          activeStep="schema"
          completedSteps={["details"]}
        />

        <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
          <div className="space-y-6">
            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div>
                <p className="text-sm font-semibold text-blue-600">
                  Dataset details
                </p>

                <h2 className="mt-2 text-xl font-bold text-slate-950">
                  Name and generation size
                </h2>

                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Provide a recognizable dataset name and the number of
                  synthetic rows to generate.
                </p>
              </div>

              <div className="mt-6 grid gap-5 md:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">
                    Dataset name
                  </span>

                  <input
                    value={datasetName}
                    onChange={(event) =>
                      onDatasetNameChange(event.target.value)
                    }
                    autoComplete="off"
                    placeholder="Customer test dataset"
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">
                    Row count
                  </span>

                  <input
                    type="number"
                    min="1"
                    max={maximumRowCount}
                    value={rowCount}
                    onChange={(event) =>
                      onRowCountChange(event.target.value)
                    }
                    placeholder="1000"
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />

                  <p className="mt-2 text-xs text-slate-500">
                    Maximum allowed:{" "}
                    {maximumRowCount.toLocaleString()} rows
                  </p>
                </label>
              </div>
            </section>

            {errorMessage && (
              <div
                role="alert"
                className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700"
              >
                {errorMessage}
              </div>
            )}

            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-blue-600">
                    Schema configuration
                  </p>

                  <h2 className="mt-2 text-xl font-bold text-slate-950">
                    Configure dataset columns
                  </h2>

                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                    Add fields, apply suggested data types, and open
                    settings only when a column needs more control.
                  </p>
                </div>

                <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-600">
                  {columns.length}{" "}
                  {columns.length === 1 ? "column" : "columns"}
                </span>
              </div>

              <div className="mt-6">
                <ColumnEditor
                  columns={columns}
                  onAddColumn={onAddColumn}
                  onUpdateColumn={onUpdateColumn}
                  onToggleColumnBoolean={onToggleColumnBoolean}
                  onDeleteColumn={onDeleteColumn}
                />
              </div>
            </section>
          </div>

          <aside className="space-y-4 xl:sticky xl:top-24 xl:self-start">
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-sm font-bold text-slate-900">
                Schema summary
              </h2>

              <dl className="mt-4 space-y-4">
                <div className="flex items-center justify-between gap-4">
                  <dt className="text-sm text-slate-500">
                    Source
                  </dt>

                  <dd className="text-sm font-semibold text-slate-800">
                    {isCsvSource ? "CSV" : "Manual"}
                  </dd>
                </div>

                <div className="flex items-center justify-between gap-4">
                  <dt className="text-sm text-slate-500">
                    Columns
                  </dt>

                  <dd className="text-sm font-semibold text-slate-800">
                    {columns.length}
                  </dd>
                </div>

                <div className="flex items-center justify-between gap-4">
                  <dt className="text-sm text-slate-500">
                    Rows
                  </dt>

                  <dd className="text-sm font-semibold text-slate-800">
                    {rowCount || "Not set"}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="rounded-3xl border border-blue-200 bg-blue-50 p-5">
              <h2 className="text-sm font-bold text-blue-900">
                Helpful guidance
              </h2>

              <ul className="mt-3 space-y-3 text-xs leading-5 text-blue-800">
                <li className="flex gap-2">
                  <span aria-hidden="true">✓</span>
                  Use clear names such as customer_id or email.
                </li>

                <li className="flex gap-2">
                  <span aria-hidden="true">✓</span>
                  Review suggested types before continuing.
                </li>

                <li className="flex gap-2">
                  <span aria-hidden="true">✓</span>
                  Open Configure only for constraints or advanced
                  generation rules.
                </li>
              </ul>
            </section>
          </aside>
        </div>
      </div>

      <footer className="sticky bottom-0 z-20 border-t border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <p className="text-sm font-semibold text-slate-800">
              Schema configuration
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Continue after reviewing every column.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onBack}
              className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200"
            >
              Back
            </button>

            <button
              type="button"
              onClick={onContinue}
              className="rounded-2xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100"
            >
              Continue to test cases
            </button>
          </div>
        </div>
      </footer>
    </section>
  )
}


export default SchemaBuilderPage