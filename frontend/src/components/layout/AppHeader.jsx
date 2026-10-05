import ThemeToggle from "../theme/ThemeToggle"


function AppHeader({
  title,
  description,
  actions,
  isDarkMode,
  onToggleTheme,
  onOpenSidebar
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
      <div className="flex min-h-[72px] items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onOpenSidebar}
            aria-label="Open navigation"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-lg text-slate-600 transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:focus:ring-blue-950 lg:hidden"
          >
            ☰
          </button>

          <div className="min-w-0">
            <h1 className="truncate text-lg font-bold text-slate-950 dark:text-white sm:text-xl">
              {title}
            </h1>

            {description && (
              <p className="mt-0.5 hidden truncate text-xs text-slate-500 dark:text-slate-400 sm:block">
                {description}
              </p>
            )}
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {actions}

          <ThemeToggle
            isDarkMode={isDarkMode}
            onToggle={onToggleTheme}
            compact
          />

          <button
            type="button"
            aria-label="User menu placeholder"
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-xs font-bold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:bg-blue-600 dark:hover:bg-blue-500 dark:focus:ring-blue-950"
          >
            TA
          </button>
        </div>
      </div>
    </header>
  )
}


export default AppHeader