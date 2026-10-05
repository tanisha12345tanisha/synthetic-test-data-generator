function SourceCard({
  badge,
  badgeClasses,
  title,
  description,
  actionLabel,
  onClick
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 text-left shadow-lg shadow-slate-200/50 transition duration-200 hover:-translate-y-1 hover:border-blue-300 hover:shadow-2xl hover:shadow-blue-100/70 focus:outline-none focus:ring-4 focus:ring-blue-100"
    >
      <div
        aria-hidden="true"
        className="absolute -right-12 -top-12 h-32 w-32 rounded-full bg-blue-50 opacity-0 transition group-hover:opacity-100"
      />

      <div
        className={`relative flex h-14 w-14 items-center justify-center rounded-2xl text-sm font-bold ${badgeClasses}`}
      >
        {badge}
      </div>

      <div className="relative mt-6">
        <h3 className="text-2xl font-bold text-slate-950">
          {title}
        </h3>

        <p className="mt-3 text-sm leading-6 text-slate-600">
          {description}
        </p>

        <div className="mt-6 flex items-center gap-2 text-sm font-semibold text-blue-600 transition group-hover:text-blue-700">
          <span>
            {actionLabel}
          </span>

          <span
            aria-hidden="true"
            className="transition-transform group-hover:translate-x-1"
          >
            →
          </span>
        </div>
      </div>
    </button>
  )
}


function FeatureBadge({
  children
}) {
  return (
    <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm">
      {children}
    </span>
  )
}


function SchemaSourceSelection({
  onUploadCsv,
  onCreateManual
}) {
  return (
    <section className="mx-auto max-w-6xl px-6 py-12 sm:py-16">
      <div className="text-center">
        <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-blue-700">
          <span
            aria-hidden="true"
            className="h-2 w-2 rounded-full bg-blue-600"
          />

          Synthetic-only generation
        </div>

        <h1 className="mx-auto mt-6 max-w-4xl text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">
          Create realistic test data without using production records
        </h1>

        <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-600">
          Start by uploading a sample CSV for schema inference or build
          a custom schema manually. Every generated row remains
          synthetic and explainable.
        </p>

        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <FeatureBadge>
            Manual schema
          </FeatureBadge>

          <FeatureBadge>
            CSV inference
          </FeatureBadge>

          <FeatureBadge>
            Controlled test cases
          </FeatureBadge>

          <FeatureBadge>
            Quality validation
          </FeatureBadge>

          <FeatureBadge>
            CSV, JSON and PSV export
          </FeatureBadge>
        </div>
      </div>

      <div className="mt-12 grid gap-6 md:grid-cols-2">
        <SourceCard
          badge="CSV"
          badgeClasses="bg-blue-50 text-blue-700"
          title="Upload CSV"
          description="Infer column names, data types, ranges, categories, constraints, and date windows from a mock or sample CSV file."
          actionLabel="Upload and infer schema"
          onClick={onUploadCsv}
        />

        <SourceCard
          badge="+"
          badgeClasses="bg-emerald-50 text-2xl text-emerald-700"
          title="Create schema manually"
          description="Define every column, select supported data types, configure constraints, and control distributions from the beginning."
          actionLabel="Open schema builder"
          onClick={onCreateManual}
        />
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
          <p className="text-sm font-semibold text-slate-900">
            Privacy-safe
          </p>

          <p className="mt-1 text-xs leading-5 text-slate-500">
            Uploaded sample rows are used only for schema inference and
            are not copied into generated output.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
          <p className="text-sm font-semibold text-slate-900">
            Rule-based
          </p>

          <p className="mt-1 text-xs leading-5 text-slate-500">
            Data generation follows explicit types, constraints,
            distributions, and case percentages.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
          <p className="text-sm font-semibold text-slate-900">
            Test-ready
          </p>

          <p className="mt-1 text-xs leading-5 text-slate-500">
            Preview generated rows, inspect quality results, and
            download the complete dataset.
          </p>
        </div>
      </div>
    </section>
  )
}


export default SchemaSourceSelection