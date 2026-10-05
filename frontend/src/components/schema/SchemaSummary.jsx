function BooleanValue({ value }) {
  return (
    <span
      className={
        value
          ? "font-medium text-emerald-700"
          : "text-slate-500"
      }
    >
      {value ? "Yes" : "No"}
    </span>
  )
}


function SchemaSummary({
  datasetName,
  rowCount,
  columns,
  schemaPreview,
  onDatasetNameChange,
  onRowCountChange,
  onEditSchema,
  maximumRowCount = 10000
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-blue-600">
            Dataset setup
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Review schema before case configuration
          </h2>

          <p className="mt-2 text-sm text-slate-600">
            Schema is visible first. You can edit it any time before generation.
          </p>
        </div>

        <button
          type="button"
          onClick={onEditSchema}
          className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-blue-100"
        >
          Edit Schema
        </button>
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
            className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
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
            className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
          />

          <p className="mt-1 text-xs text-slate-500">
            Maximum allowed:{" "}
            {maximumRowCount.toLocaleString()} rows
          </p>
        </label>
      </div>

      <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200">
        <div className="flex items-center justify-between gap-4 bg-slate-50 px-4 py-3">
          <p className="text-sm font-bold text-slate-700">
            Schema columns
          </p>

          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600">
            {columns.length}
          </span>
        </div>

        <div className="max-h-80 overflow-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="sticky top-0 z-10 bg-white">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">
                  Name
                </th>

                <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">
                  Type
                </th>

                <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">
                  Required
                </th>

                <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">
                  Nullable
                </th>

                <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">
                  Unique
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100 bg-white">
              {columns.map((column) => (
                <tr
                  key={column.id}
                  className="transition hover:bg-slate-50"
                >
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {column.name}
                  </td>

                  <td className="px-4 py-3">
                    <span className="rounded-lg bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700">
                      {column.type}
                    </span>
                  </td>

                  <td className="px-4 py-3">
                    <BooleanValue
                      value={column.required}
                    />
                  </td>

                  <td className="px-4 py-3">
                    <BooleanValue
                      value={column.nullable}
                    />
                  </td>

                  <td className="px-4 py-3">
                    <BooleanValue
                      value={column.unique}
                    />
                  </td>
                </tr>
              ))}

              {columns.length === 0 && (
                <tr>
                  <td
                    colSpan="5"
                    className="px-4 py-8 text-center text-sm text-slate-500"
                  >
                    No schema columns are available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <details className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <summary className="cursor-pointer text-sm font-semibold text-slate-700">
          View request JSON
        </summary>

        <pre className="mt-4 max-h-96 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-6 text-slate-100">
          {JSON.stringify(
            schemaPreview,
            null,
            2
          )}
        </pre>
      </details>
    </section>
  )
}


export default SchemaSummary