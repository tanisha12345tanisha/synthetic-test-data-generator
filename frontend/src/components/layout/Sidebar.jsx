const NAVIGATION_ITEMS = [
  {
    key: "dashboard",
    label: "Dashboard",
    icon: "D",
    disabled: true
  },
  {
    key: "generator",
    label: "Data generator",
    icon: "G",
    disabled: false
  },
  {
    key: "datasets",
    label: "Datasets",
    icon: "DS",
    disabled: true
  },
  {
    key: "templates",
    label: "Templates",
    icon: "T",
    disabled: true
  },
  {
    key: "connections",
    label: "Connections",
    icon: "C",
    disabled: true
  },
  {
    key: "history",
    label: "Generation history",
    icon: "H",
    disabled: true
  },
  {
    key: "reports",
    label: "Reports",
    icon: "R",
    disabled: true
  }
]


const SECONDARY_ITEMS = [
  {
    key: "settings",
    label: "Settings",
    icon: "S",
    disabled: true
  },
  {
    key: "help",
    label: "Help",
    icon: "?",
    disabled: true
  }
]


function NavigationItem({
  item,
  activeItem,
  onSelect
}) {
  const isActive =
    activeItem === item.key

  return (
    <button
      type="button"
      onClick={() => {
        if (!item.disabled) {
          onSelect(item.key)
        }
      }}
      disabled={item.disabled}
      aria-current={
        isActive ? "page" : undefined
      }
      className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition focus:outline-none focus:ring-4 focus:ring-blue-900 ${
        isActive
          ? "bg-blue-600 text-white shadow-lg shadow-blue-950/30"
          : item.disabled
            ? "cursor-not-allowed text-slate-500 opacity-65"
            : "text-slate-300 hover:bg-slate-800 hover:text-white"
      }`}
    >
      <span
        aria-hidden="true"
        className={`flex h-8 min-w-8 items-center justify-center rounded-lg px-1 text-[10px] font-bold ${
          isActive
            ? "bg-white/15 text-white"
            : "bg-slate-800 text-slate-400 group-hover:text-slate-200"
        }`}
      >
        {item.icon}
      </span>

      <span className="min-w-0 flex-1 truncate">
        {item.label}
      </span>

      {item.disabled && (
        <span className="rounded-md border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-slate-500">
          Soon
        </span>
      )}
    </button>
  )
}


function Sidebar({
  isOpen,
  activeItem = "generator",
  onSelect,
  onClose
}) {
  return (
    <>
      {isOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        aria-label="Application navigation"
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-slate-950 text-white transition-transform duration-200 lg:translate-x-0 ${
          isOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
      >
        <div className="flex h-[73px] shrink-0 items-center justify-between border-b border-slate-800 px-5">
          <button
            type="button"
            onClick={() =>
              onSelect("generator")
            }
            className="flex min-w-0 items-center gap-3 rounded-xl text-left focus:outline-none focus:ring-4 focus:ring-blue-900"
          >
            <span
              aria-hidden="true"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold text-white shadow-lg shadow-blue-950/40"
            >
              SD
            </span>

            <span className="min-w-0">
              <span className="block truncate text-sm font-bold text-white">
                Synthetic Data
              </span>

              <span className="block truncate text-xs text-slate-400">
                Test-data platform
              </span>
            </span>
          </button>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close sidebar"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-lg text-slate-400 transition hover:bg-slate-800 hover:text-white focus:outline-none focus:ring-4 focus:ring-blue-900 lg:hidden"
          >
            ×
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-4 py-5">
          <p className="px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
            Workspace
          </p>

          <div className="mt-3 space-y-1">
            {NAVIGATION_ITEMS.map(
              (item) => (
                <NavigationItem
                  key={item.key}
                  item={item}
                  activeItem={activeItem}
                  onSelect={onSelect}
                />
              )
            )}
          </div>

          <div className="my-5 border-t border-slate-800" />

          <p className="px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
            Support
          </p>

          <div className="mt-3 space-y-1">
            {SECONDARY_ITEMS.map(
              (item) => (
                <NavigationItem
                  key={item.key}
                  item={item}
                  activeItem={activeItem}
                  onSelect={onSelect}
                />
              )
            )}
          </div>
        </nav>

        <div className="shrink-0 border-t border-slate-800 p-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="flex items-center gap-2">
              <span
                aria-hidden="true"
                className="h-2 w-2 rounded-full bg-emerald-400"
              />

              <p className="text-xs font-semibold text-slate-200">
                Synthetic-only mode
              </p>
            </div>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Rule-based generation with no production-row reuse.
            </p>
          </div>
        </div>
      </aside>
    </>
  )
}


export default Sidebar