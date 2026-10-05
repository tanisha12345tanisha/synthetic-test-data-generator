import { useEffect, useMemo, useRef, useState } from "react"

import {
  COMMON_DATA_TYPES,
  DATA_TYPE_GROUPS,
  getDataTypeDetails
} from "../../constants/dataTypes"


function TypeOption({
  type,
  selected,
  onSelect
}) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={selected}
      onClick={() => onSelect(type.value)}
      className={`flex w-full items-start gap-3 rounded-2xl border p-3 text-left transition focus:outline-none focus:ring-4 focus:ring-blue-100 ${
        selected
          ? "border-blue-300 bg-blue-50"
          : "border-slate-200 bg-white hover:border-blue-200 hover:bg-slate-50"
      }`}
    >
      <span
        aria-hidden="true"
        className={`flex h-10 min-w-10 shrink-0 items-center justify-center rounded-xl px-2 text-xs font-bold ${
          selected
            ? "bg-blue-600 text-white"
            : "bg-slate-100 text-slate-600"
        }`}
      >
        {type.icon}
      </span>

      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-slate-900">
          {type.label}
        </span>

        <span className="mt-1 block text-xs leading-5 text-slate-500">
          {type.description}
        </span>
      </span>

      {selected && (
        <span
          aria-hidden="true"
          className="mt-2 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white"
        >
          ✓
        </span>
      )}
    </button>
  )
}


function CommonTypeButton({
  type,
  selected,
  onSelect
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(type.value)}
      className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-semibold transition focus:outline-none focus:ring-4 focus:ring-blue-100 ${
        selected
          ? "border-blue-600 bg-blue-600 text-white"
          : "border-slate-200 bg-white text-slate-700 hover:border-blue-300 hover:bg-blue-50"
      }`}
    >
      <span
        aria-hidden="true"
        className={`flex h-6 min-w-6 items-center justify-center rounded-lg px-1 text-[10px] font-bold ${
          selected
            ? "bg-white/20 text-white"
            : "bg-slate-100 text-slate-500"
        }`}
      >
        {type.icon}
      </span>

      {type.shortLabel}
    </button>
  )
}


function DataTypePicker({
  value,
  onChange,
  suggestedType = "",
  disabled = false
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchText, setSearchText] = useState("")
  const containerRef = useRef(null)
  const searchInputRef = useRef(null)

  const selectedType = getDataTypeDetails(value)

  const commonTypes = useMemo(
    () =>
      COMMON_DATA_TYPES.map((type) =>
        getDataTypeDetails(type)
      ),
    []
  )

  const filteredGroups = useMemo(() => {
    const normalizedSearch = searchText
      .trim()
      .toLowerCase()

    if (!normalizedSearch) {
      return DATA_TYPE_GROUPS
    }

    return DATA_TYPE_GROUPS
      .map((group) => ({
        ...group,
        types: group.types.filter((type) => {
          const searchableText = [
            type.value,
            type.label,
            type.shortLabel,
            type.description,
            group.label
          ]
            .join(" ")
            .toLowerCase()

          return searchableText.includes(normalizedSearch)
        })
      }))
      .filter((group) => group.types.length > 0)
  }, [searchText])

  const totalFilteredTypes = filteredGroups.reduce(
    (total, group) => total + group.types.length,
    0
  )

  useEffect(() => {
    function handleOutsideClick(event) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target)
      ) {
        setIsOpen(false)
        setSearchText("")
      }
    }

    function handleEscape(event) {
      if (event.key === "Escape") {
        setIsOpen(false)
        setSearchText("")
      }
    }

    document.addEventListener(
      "mousedown",
      handleOutsideClick
    )

    document.addEventListener(
      "keydown",
      handleEscape
    )

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick
      )

      document.removeEventListener(
        "keydown",
        handleEscape
      )
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      window.setTimeout(() => {
        searchInputRef.current?.focus()
      }, 0)
    }
  }, [isOpen])

  function handleSelect(type) {
    onChange(type)
    setIsOpen(false)
    setSearchText("")
  }

  function handleToggle() {
    if (disabled) {
      return
    }

    setIsOpen((currentValue) => !currentValue)
  }

  return (
    <div
      ref={containerRef}
      className="relative"
    >
      <button
        type="button"
        onClick={handleToggle}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        className={`flex w-full items-center justify-between gap-3 rounded-2xl border bg-white px-4 py-3 text-left transition focus:outline-none focus:ring-4 focus:ring-blue-100 ${
          isOpen
            ? "border-blue-500"
            : "border-slate-200 hover:border-slate-300"
        } ${
          disabled
            ? "cursor-not-allowed bg-slate-100 opacity-70"
            : ""
        }`}
      >
        <span className="flex min-w-0 items-center gap-3">
          <span
            aria-hidden="true"
            className={`flex h-9 min-w-9 shrink-0 items-center justify-center rounded-xl px-2 text-xs font-bold ${
              value
                ? "bg-blue-50 text-blue-700"
                : "bg-slate-100 text-slate-500"
            }`}
          >
            {selectedType.icon}
          </span>

          <span className="min-w-0">
            <span
              className={`block truncate text-sm font-semibold ${
                value
                  ? "text-slate-900"
                  : "text-slate-500"
              }`}
            >
              {value
                ? selectedType.label
                : "Choose data type"}
            </span>

            <span className="mt-0.5 block truncate text-xs text-slate-500">
              {value
                ? selectedType.description
                : "Search or select from grouped types"}
            </span>
          </span>
        </span>

        <span
          aria-hidden="true"
          className={`shrink-0 text-sm text-slate-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        >
          ▾
        </span>
      </button>

      {suggestedType &&
        suggestedType !== value &&
        !isOpen && (
          <button
            type="button"
            onClick={() => handleSelect(suggestedType)}
            className="mt-2 inline-flex items-center gap-2 rounded-xl border border-violet-200 bg-violet-50 px-3 py-2 text-xs font-semibold text-violet-700 transition hover:bg-violet-100 focus:outline-none focus:ring-4 focus:ring-violet-100"
          >
            <span aria-hidden="true">
              ✦
            </span>

            Suggested:{" "}
            {getDataTypeDetails(suggestedType).shortLabel}

            <span
              aria-hidden="true"
              className="text-violet-400"
            >
              Apply
            </span>
          </button>
        )}

      {isOpen && (
        <div className="absolute left-0 right-0 z-50 mt-2 max-h-[520px] overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl shadow-slate-300/70">
          <div className="border-b border-slate-200 p-4">
            <label className="relative block">
              <span className="sr-only">
                Search data types
              </span>

              <span
                aria-hidden="true"
                className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
              >
                ⌕
              </span>

              <input
                ref={searchInputRef}
                value={searchText}
                onChange={(event) =>
                  setSearchText(event.target.value)
                }
                placeholder="Search data types..."
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100"
              />
            </label>

            {!searchText && (
              <div className="mt-4">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Common types
                </p>

                <div className="mt-2 flex flex-wrap gap-2">
                  {commonTypes.map((type) => (
                    <CommonTypeButton
                      key={type.value}
                      type={type}
                      selected={value === type.value}
                      onSelect={handleSelect}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          <div
            role="listbox"
            aria-label="Data types"
            className="max-h-[350px] overflow-y-auto p-4"
          >
            {filteredGroups.map((group) => (
              <section
                key={group.key}
                className="mb-6 last:mb-0"
              >
                <div className="mb-3">
                  <h4 className="text-sm font-bold text-slate-900">
                    {group.label}
                  </h4>

                  <p className="mt-1 text-xs text-slate-500">
                    {group.description}
                  </p>
                </div>

                <div className="grid gap-2 sm:grid-cols-2">
                  {group.types.map((type) => (
                    <TypeOption
                      key={type.value}
                      type={type}
                      selected={value === type.value}
                      onSelect={handleSelect}
                    />
                  ))}
                </div>
              </section>
            ))}

            {totalFilteredTypes === 0 && (
              <div className="px-4 py-10 text-center">
                <p className="text-sm font-semibold text-slate-700">
                  No matching data type
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  Try searching with a different name or category.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


export default DataTypePicker