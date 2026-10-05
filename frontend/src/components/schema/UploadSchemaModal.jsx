function UploadSchemaModal({
  isOpen,
  datasetName,
  rowCount,
  errorMessage,
  isInferringSchema,
  maximumRowCount = 10000,
  onDatasetNameChange,
  onRowCountChange,
  onFileChange,
  onClose
}) {
  if (!isOpen) {
    return null
  }

  return (
    <div
      role="presentation"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 px-4 py-6 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          !isInferringSchema
        ) {
          onClose()
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-schema-title"
        aria-describedby="upload-schema-description"
        className="w-full max-w-2xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl"
      >
        <header className="flex items-start justify-between gap-5 border-b border-slate-200 px-6 py-5">
          <div>
            <p className="text-sm font-semibold text-blue-600">
              CSV schema inference
            </p>

            <h2
              id="upload-schema-title"
              className="mt-2 text-2xl font-bold text-slate-950"
            >
              Create a schema from CSV
            </h2>

            <p
              id="upload-schema-description"
              className="mt-2 text-sm leading-6 text-slate-600"
            >
              Upload a mock or sample CSV file to infer column names,
              data types, constraints, ranges, and category values.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isInferringSchema}
            aria-label="Close CSV upload dialog"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-lg font-semibold text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            ×
          </button>
        </header>

        <div className="px-6 py-6">
          <div className="rounded-2xl border border-blue-200 bg-blue-50 px-4 py-4">
            <div className="flex gap-3">
              <div
                aria-hidden="true"
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-blue-200 bg-white text-sm font-bold text-blue-700"
              >
                i
              </div>

              <div>
                <p className="text-sm font-semibold text-blue-800">
                  Synthetic-only processing
                </p>

                <p className="mt-1 text-sm leading-6 text-blue-700">
                  The uploaded file is used only to infer the schema.
                  Source rows are not copied into the generated
                  output. Use mock or sample files, not production
                  data.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Dataset name
              </span>

              <input
                value={datasetName}
                onChange={(event) =>
                  onDatasetNameChange(event.target.value)
                }
                disabled={isInferringSchema}
                autoComplete="off"
                placeholder="Customer test dataset"
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-100"
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
                disabled={isInferringSchema}
                placeholder="1000"
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-100"
              />

              <p className="mt-2 text-xs text-slate-500">
                Maximum allowed:{" "}
                {maximumRowCount.toLocaleString()} rows
              </p>
            </label>
          </div>

          {errorMessage && (
            <div
              role="alert"
              className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
            >
              {errorMessage}
            </div>
          )}

          <label
            className={`mt-6 flex flex-col items-center justify-center rounded-3xl border-2 border-dashed px-6 py-12 text-center transition ${
              isInferringSchema
                ? "cursor-wait border-blue-300 bg-blue-50"
                : "cursor-pointer border-slate-300 bg-slate-50 hover:border-blue-400 hover:bg-blue-50/60"
            }`}
          >
            <div
              aria-hidden="true"
              className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-lg font-bold text-blue-700 shadow-sm"
            >
              CSV
            </div>

            <p className="mt-4 text-sm font-semibold text-slate-900">
              {isInferringSchema
                ? "Inferring schema..."
                : "Choose a CSV file"}
            </p>

            <p className="mt-2 max-w-md text-xs leading-5 text-slate-500">
              Only files with the .csv extension are supported.
              Review and edit all inferred fields before generation.
            </p>

            {isInferringSchema && (
              <div
                role="status"
                aria-live="polite"
                className="mt-4 flex items-center gap-2 text-sm font-medium text-blue-700"
              >
                <span
                  aria-hidden="true"
                  className="h-4 w-4 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600"
                />

                Processing file
              </div>
            )}

            <input
              type="file"
              accept=".csv,text/csv"
              onChange={onFileChange}
              disabled={isInferringSchema}
              className="hidden"
            />
          </label>
        </div>

        <footer className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 bg-slate-50 px-6 py-5">
          <p className="text-xs leading-5 text-slate-500">
            The inferred schema remains editable before generation.
          </p>

          <button
            type="button"
            onClick={onClose}
            disabled={isInferringSchema}
            className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Cancel
          </button>
        </footer>
      </section>
    </div>
  )
}


export default UploadSchemaModal