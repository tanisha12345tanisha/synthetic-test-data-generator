import {
  hasAdvancedFields,
  supportsBooleanProbability,
  supportsCategoryValues,
  supportsDateRange,
  supportsLengthRange,
  supportsNumericRange,
  supportsPattern,
  supportsPrefix
} from "../../constants/dataTypes"


const inputClasses =
  "mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"

const selectClasses =
  "mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"


function ToggleSetting({
  label,
  description,
  active,
  onClick
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`flex w-full items-center justify-between gap-4 rounded-2xl border p-4 text-left transition focus:outline-none focus:ring-4 focus:ring-blue-100 ${
        active
          ? "border-blue-300 bg-blue-50"
          : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
      }`}
    >
      <span>
        <span className="block text-sm font-semibold text-slate-900">
          {label}
        </span>

        <span className="mt-1 block text-xs leading-5 text-slate-500">
          {description}
        </span>
      </span>

      <span
        aria-hidden="true"
        className={`relative h-6 w-11 shrink-0 rounded-full transition ${
          active
            ? "bg-blue-600"
            : "bg-slate-300"
        }`}
      >
        <span
          className={`absolute top-1 h-4 w-4 rounded-full bg-white shadow transition-transform ${
            active
              ? "translate-x-6"
              : "translate-x-1"
          }`}
        />
      </span>
    </button>
  )
}


function ConstraintSettings({
  column,
  onToggle
}) {
  return (
    <div>
      <div>
        <h4 className="text-sm font-bold text-slate-900">
          Constraints
        </h4>

        <p className="mt-1 text-xs leading-5 text-slate-500">
          Configure whether this field is mandatory, optional, or
          unique.
        </p>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <ToggleSetting
          label="Required"
          description="Every generated row must contain a value."
          active={column.required}
          onClick={() =>
            onToggle(
              column.id,
              "required"
            )
          }
        />

        <ToggleSetting
          label="Nullable"
          description="Some generated rows may contain null."
          active={column.nullable}
          onClick={() =>
            onToggle(
              column.id,
              "nullable"
            )
          }
        />

        <ToggleSetting
          label="Unique"
          description="Generated values must not repeat."
          active={column.unique}
          onClick={() =>
            onToggle(
              column.id,
              "unique"
            )
          }
        />
      </div>
    </div>
  )
}


function NumericSettings({
  column,
  onUpdate
}) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <label className="block">
        <span className="text-sm font-medium text-slate-700">
          Minimum value
        </span>

        <input
          type="number"
          value={column.min}
          onChange={(event) =>
            onUpdate(
              column.id,
              "min",
              event.target.value
            )
          }
          placeholder="Minimum"
          className={inputClasses}
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-slate-700">
          Maximum value
        </span>

        <input
          type="number"
          value={column.max}
          onChange={(event) =>
            onUpdate(
              column.id,
              "max",
              event.target.value
            )
          }
          placeholder="Maximum"
          className={inputClasses}
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-slate-700">
          Distribution
        </span>

        <select
          value={column.distribution_type}
          onChange={(event) =>
            onUpdate(
              column.id,
              "distribution_type",
              event.target.value
            )
          }
          className={selectClasses}
        >
          <option value="">
            Automatic
          </option>

          <option value="uniform">
            Uniform
          </option>

          <option value="normal">
            Normal
          </option>

          <option value="exponential">
            Exponential
          </option>
        </select>
      </label>

      {column.distribution_type === "normal" && (
        <>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">
              Mean
            </span>

            <input
              type="number"
              value={column.mean}
              onChange={(event) =>
                onUpdate(
                  column.id,
                  "mean",
                  event.target.value
                )
              }
              placeholder="Mean"
              className={inputClasses}
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">
              Standard deviation
            </span>

            <input
              type="number"
              min="0"
              value={column.std}
              onChange={(event) =>
                onUpdate(
                  column.id,
                  "std",
                  event.target.value
                )
              }
              placeholder="Standard deviation"
              className={inputClasses}
            />
          </label>
        </>
      )}

      {column.distribution_type === "exponential" && (
        <label className="block">
          <span className="text-sm font-medium text-slate-700">
            Mean or scale
          </span>

          <input
            type="number"
            value={column.mean}
            onChange={(event) =>
              onUpdate(
                column.id,
                "mean",
                event.target.value
              )
            }
            placeholder="Mean or scale"
            className={inputClasses}
          />
        </label>
      )}
    </div>
  )
}


function LengthSettings({
  column,
  onUpdate
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="block">
        <span className="text-sm font-medium text-slate-700">
          Minimum length
        </span>

        <input
          type="number"
          min="0"
          value={column.min_length}
          onChange={(event) =>
            onUpdate(
              column.id,
              "min_length",
              event.target.value
            )
          }
          placeholder="Minimum length"
          className={inputClasses}
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-slate-700">
          Maximum length
        </span>

        <input
          type="number"
          min="0"
          value={column.max_length}
          onChange={(event) =>
            onUpdate(
              column.id,
              "max_length",
              event.target.value
            )
          }
          placeholder="Maximum length"
          className={inputClasses}
        />
      </label>
    </div>
  )
}


function BooleanSettings({
  column,
  onUpdate
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">
        True probability
      </span>

      <div className="relative mt-2">
        <input
          type="number"
          min="0"
          max="100"
          value={column.true_probability}
          onChange={(event) =>
            onUpdate(
              column.id,
              "true_probability",
              event.target.value
            )
          }
          placeholder="50"
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 pr-10 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
        />

        <span
          aria-hidden="true"
          className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm font-semibold text-slate-400"
        >
          %
        </span>
      </div>
    </label>
  )
}


function DateSettings({
  column,
  onUpdate
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="block">
        <span className="text-sm font-medium text-slate-700">
          Start date
        </span>

        <input
          type="date"
          value={column.start_date}
          onChange={(event) =>
            onUpdate(
              column.id,
              "start_date",
              event.target.value
            )
          }
          className={inputClasses}
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-slate-700">
          End date
        </span>

        <input
          type="date"
          value={column.end_date}
          onChange={(event) =>
            onUpdate(
              column.id,
              "end_date",
              event.target.value
            )
          }
          className={inputClasses}
        />
      </label>
    </div>
  )
}


function CategorySettings({
  column,
  onUpdate
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="block">
        <span className="text-sm font-medium text-slate-700">
          Allowed values
        </span>

        <input
          value={column.values}
          onChange={(event) =>
            onUpdate(
              column.id,
              "values",
              event.target.value
            )
          }
          placeholder="Active, Inactive, Blocked"
          className={inputClasses}
        />

        <p className="mt-2 text-xs text-slate-500">
          Separate values using commas.
        </p>
      </label>

      <label className="block">
        <span className="text-sm font-medium text-slate-700">
          Optional weights
        </span>

        <input
          value={column.weights}
          onChange={(event) =>
            onUpdate(
              column.id,
              "weights",
              event.target.value
            )
          }
          placeholder="Active:70, Inactive:30"
          className={inputClasses}
        />

        <p className="mt-2 text-xs text-slate-500">
          Use the format value:weight.
        </p>
      </label>
    </div>
  )
}


function PrefixSettings({
  column,
  onUpdate
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">
        ID prefix
      </span>

      <input
        value={column.prefix}
        onChange={(event) =>
          onUpdate(
            column.id,
            "prefix",
            event.target.value
          )
        }
        placeholder="CUST"
        className={inputClasses}
      />
    </label>
  )
}


function PatternSettings({
  column,
  onUpdate
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">
        Regular expression
      </span>

      <input
        value={column.pattern}
        onChange={(event) =>
          onUpdate(
            column.id,
            "pattern",
            event.target.value
          )
        }
        placeholder="[A-Z]{3}[0-9]{4}"
        className={inputClasses}
      />
    </label>
  )
}


function GenerationSettings({
  column,
  onUpdate
}) {
  if (!hasAdvancedFields(column.type)) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-5">
        <p className="text-sm font-semibold text-slate-700">
          Automatic generation
        </p>

        <p className="mt-1 text-xs leading-5 text-slate-500">
          This type does not require additional generation settings.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {supportsNumericRange(column.type) && (
        <NumericSettings
          column={column}
          onUpdate={onUpdate}
        />
      )}

      {supportsLengthRange(column.type) && (
        <LengthSettings
          column={column}
          onUpdate={onUpdate}
        />
      )}

      {supportsBooleanProbability(column.type) && (
        <BooleanSettings
          column={column}
          onUpdate={onUpdate}
        />
      )}

      {supportsDateRange(column.type) && (
        <DateSettings
          column={column}
          onUpdate={onUpdate}
        />
      )}

      {supportsCategoryValues(column.type) && (
        <CategorySettings
          column={column}
          onUpdate={onUpdate}
        />
      )}

      {supportsPrefix(column.type) && (
        <PrefixSettings
          column={column}
          onUpdate={onUpdate}
        />
      )}

      {supportsPattern(column.type) && (
        <PatternSettings
          column={column}
          onUpdate={onUpdate}
        />
      )}
    </div>
  )
}


function ColumnSettingsPanel({
  column,
  activeSection,
  onSectionChange,
  onUpdate,
  onToggle
}) {
  const sections = [
    {
      key: "constraints",
      label: "Constraints"
    },
    {
      key: "generation",
      label: "Generation settings"
    }
  ]

  return (
    <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200 bg-white">
      <div className="flex gap-1 border-b border-slate-200 bg-slate-50 p-2">
        {sections.map((section) => (
          <button
            key={section.key}
            type="button"
            onClick={() =>
              onSectionChange(section.key)
            }
            className={`rounded-xl px-4 py-2 text-sm font-semibold transition focus:outline-none focus:ring-4 focus:ring-blue-100 ${
              activeSection === section.key
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:bg-white/70 hover:text-slate-900"
            }`}
          >
            {section.label}
          </button>
        ))}
      </div>

      <div className="p-5">
        {activeSection === "constraints" && (
          <ConstraintSettings
            column={column}
            onToggle={onToggle}
          />
        )}

        {activeSection === "generation" && (
          <GenerationSettings
            column={column}
            onUpdate={onUpdate}
          />
        )}
      </div>
    </div>
  )
}


export default ColumnSettingsPanel