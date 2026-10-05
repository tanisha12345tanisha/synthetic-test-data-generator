function ThemeToggle({
  isDarkMode,
  onToggle,
  compact = false
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={
        isDarkMode
          ? "Switch to light theme"
          : "Switch to dark theme"
      }
      aria-pressed={isDarkMode}
      title={
        isDarkMode
          ? "Switch to light theme"
          : "Switch to dark theme"
      }
      className="inline-flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-slate-600 dark:hover:bg-slate-800 dark:focus:ring-blue-950"
    >
      <span
        aria-hidden="true"
        className={`relative flex h-7 w-12 shrink-0 items-center rounded-full transition ${
          isDarkMode
            ? "bg-blue-600"
            : "bg-slate-300"
        }`}
      >
        <span
          className={`absolute flex h-5 w-5 items-center justify-center rounded-full bg-white text-[10px] shadow transition-transform ${
            isDarkMode
              ? "translate-x-6"
              : "translate-x-1"
          }`}
        >
          {isDarkMode ? "☾" : "☀"}
        </span>
      </span>

      {!compact && (
        <span>
          {isDarkMode
            ? "Dark mode"
            : "Light mode"}
        </span>
      )}
    </button>
  )
}


export default ThemeToggle