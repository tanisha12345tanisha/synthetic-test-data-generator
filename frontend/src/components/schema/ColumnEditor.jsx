import { useState } from "react"

import {
  getDataTypeDetails,
  suggestDataType
} from "../../constants/dataTypes"

import ColumnSettingsPanel from "./ColumnSettingsPanel"
import DataTypePicker from "./DataTypePicker"


const inputClasses =
  "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"


function ConstraintBadge({
  children,
  tone = "slate"
}) {
  const toneClasses = {
    slate:
      "border-slate-200 bg-slate-100 text-slate-600",
    blue:
      "border-blue-200 bg-blue-50 text-blue-700",
    emerald:
      "border-emerald-200 bg-emerald-50 text-emerald-700",
    violet:
      "border-violet-200 bg-violet-50 text-violet-700"
  }

  return (
    <span
      className={`rounded-lg border px-2 py-1 text-[11px] font-bold uppercase tracking-wide ${
        toneClasses[tone] ||
        toneClasses.slate
      }`}
    >
      {children}
    </span>
  )
}


function ColumnSummary({
  column
}) {
  const typeDetails =
    getDataTypeDetails(column.type)

  const activeConstraints = []

  if (column.required) {
    activeConstraints.push({
      label: "Required",
      tone: "blue"
    })
  }

  if (column.nullable) {
    activeConstraints.push({
      label: "Nullable",
      tone: "slate"
    })
  }

  if (column.unique) {
    activeConstraints.push({
      label: "Unique",
      tone: "violet"
    })
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {column.type && (
        <ConstraintBadge tone="emerald">
          {typeDetails.shortLabel}
        </ConstraintBadge>
      )}

      {activeConstraints.map((constraint) => (
        <ConstraintBadge
          key={constraint.label}
          tone={constraint.tone}
        >
          {constraint.label}
        </ConstraintBadge>
      ))}

      {activeConstraints.length === 0 && (
        <span className="text-xs text-slate-400">
          Optional · Repeating values allowed
        </span>
      )}
    </div>
  )
}


function ColumnCard({
  column,
  index,
  onUpdate,
  onToggle,
  onDelete
}) {
  const [isExpanded, setIsExpanded] =
    useState(false)

  const [
    activeSettingsSection,
    setActiveSettingsSection
  ] = useState("constraints")

  const suggestedType =
    column.type
      ? ""
      : suggestDataType(column.name)

  function handleNameChange(value) {
    onUpdate(
      column.id,
      "name",
      value
    )
  }

  function handleTypeChange(type) {
    onUpdate(
      column.id,
      "type",
      type
    )

    if (
      type === "id" &&
      !column.prefix
    ) {
      const prefix = column.name
        .replace(/_?id$/i, "")
        .replace(/[^a-zA-Z0-9]/g, "")
        .slice(0, 6)
        .toUpperCase()

      if (prefix) {
        onUpdate(
          column.id,
          "prefix",
          prefix
        )
      }
    }

    if (
      type === "boolean" &&
      column.true_probability === ""
    ) {
      onUpdate(
        column.id,
        "true_probability",
        "50"
      )
    }

    setIsExpanded(true)
  }

  return (
    <article className="rounded-3xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
            Column {index + 1}
          </p>

          <h3 className="mt-1 truncate text-base font-semibold text-slate-900">
            {column.name ||
              "Unnamed column"}
          </h3>

          <div className="mt-3">
            <ColumnSummary
              column={column}
            />
          </div>
        </div>

        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={() =>
              setIsExpanded(
                (currentValue) =>
                  !currentValue
              )
            }
            aria-expanded={isExpanded}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 focus:outline-none focus:ring-4 focus:ring-blue-100"
          >
            {isExpanded
              ? "Hide settings"
              : "Configure"}
          </button>

          <button
            type="button"
            onClick={() =>
              onDelete(column.id)
            }
            aria-label={`Delete ${
              column.name ||
              `column ${index + 1}`
            }`}
            className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-100 focus:outline-none focus:ring-4 focus:ring-red-100"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <label className="block">
          <span className="text-sm font-medium text-slate-700">
            Column name
          </span>

          <input
            value={column.name}
            onChange={(event) =>
              handleNameChange(
                event.target.value
              )
            }
            placeholder="customer_id"
            className={`mt-2 ${inputClasses}`}
          />
        </label>

        <div>
          <span className="text-sm font-medium text-slate-700">
            Data type
          </span>

          <div className="mt-2">
            <DataTypePicker
              value={column.type}
              suggestedType={
                suggestedType
              }
              onChange={
                handleTypeChange
              }
            />
          </div>
        </div>
      </div>

      {isExpanded && (
        <ColumnSettingsPanel
          column={column}
          activeSection={
            activeSettingsSection
          }
          onSectionChange={
            setActiveSettingsSection
          }
          onUpdate={
            onUpdate
          }
          onToggle={
            onToggle
          }
        />
      )}
    </article>
  )
}


function ColumnEditor({
  columns,
  onAddColumn,
  onUpdateColumn,
  onToggleColumnBoolean,
  onDeleteColumn
}) {
  return (
    <div className="space-y-4">
      {columns.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-xl font-bold text-blue-700">
            +
          </div>

          <p className="mt-4 text-sm font-semibold text-slate-700">
            No columns added yet
          </p>

          <p className="mt-2 text-sm text-slate-500">
            Add the first column and the application will suggest a
            suitable data type from its name.
          </p>

          <button
            type="button"
            onClick={onAddColumn}
            className="mt-5 rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100"
          >
            Add first column
          </button>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-800">
                Schema columns
              </p>

              <p className="mt-1 text-xs text-slate-500">
                {columns.length}{" "}
                {columns.length === 1
                  ? "column"
                  : "columns"}{" "}
                configured
              </p>
            </div>

            <button
              type="button"
              onClick={onAddColumn}
              className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100"
            >
              Add column
            </button>
          </div>

          {columns.map(
            (column, index) => (
              <ColumnCard
                key={column.id}
                column={column}
                index={index}
                onUpdate={
                  onUpdateColumn
                }
                onToggle={
                  onToggleColumnBoolean
                }
                onDelete={
                  onDeleteColumn
                }
              />
            )
          )}
        </>
      )}
    </div>
  )
}


export default ColumnEditor