const BUILDER_STEPS = [
  {
    key: "details",
    label: "Details",
    description: "Dataset information"
  },
  {
    key: "schema",
    label: "Schema",
    description: "Columns and settings"
  },
  {
    key: "cases",
    label: "Test cases",
    description: "Coverage percentages"
  },
  {
    key: "review",
    label: "Review",
    description: "Validate and generate"
  }
]


function BuilderProgress({
  activeStep = "schema",
  completedSteps = []
}) {
  const activeStepIndex = BUILDER_STEPS.findIndex(
    (step) => step.key === activeStep
  )

  return (
    <nav
      aria-label="Dataset builder progress"
      className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
    >
      <ol className="grid md:grid-cols-4">
        {BUILDER_STEPS.map((step, index) => {
          const isActive = step.key === activeStep

          const isComplete =
            completedSteps.includes(step.key) ||
            index < activeStepIndex

          return (
            <li
              key={step.key}
              aria-current={isActive ? "step" : undefined}
              className={`relative border-b border-slate-200 px-5 py-4 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0 ${
                isActive
                  ? "bg-blue-50"
                  : "bg-white"
              }`}
            >
              <div className="flex items-center gap-3">
                <span
                  aria-hidden="true"
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-sm font-bold ${
                    isComplete
                      ? "bg-emerald-600 text-white"
                      : isActive
                        ? "bg-blue-600 text-white"
                        : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {isComplete ? "✓" : index + 1}
                </span>

                <span className="min-w-0">
                  <span
                    className={`block text-sm font-semibold ${
                      isActive
                        ? "text-blue-800"
                        : isComplete
                          ? "text-emerald-700"
                          : "text-slate-700"
                    }`}
                  >
                    {step.label}
                  </span>

                  <span className="mt-0.5 block truncate text-xs text-slate-500">
                    {step.description}
                  </span>
                </span>
              </div>

              {isActive && (
                <span
                  aria-hidden="true"
                  className="absolute bottom-0 left-0 h-1 w-full bg-blue-600"
                />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}


export default BuilderProgress