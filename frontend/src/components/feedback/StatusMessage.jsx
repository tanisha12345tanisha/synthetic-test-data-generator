const MESSAGE_STYLES = {
  error: {
    container:
      "border-red-200 bg-red-50 text-red-700",
    icon:
      "border-red-200 bg-red-100 text-red-700",
    symbol: "!"
  },
  success: {
    container:
      "border-emerald-200 bg-emerald-50 text-emerald-700",
    icon:
      "border-emerald-200 bg-emerald-100 text-emerald-700",
    symbol: "✓"
  },
  warning: {
    container:
      "border-amber-200 bg-amber-50 text-amber-700",
    icon:
      "border-amber-200 bg-amber-100 text-amber-700",
    symbol: "!"
  },
  info: {
    container:
      "border-blue-200 bg-blue-50 text-blue-700",
    icon:
      "border-blue-200 bg-blue-100 text-blue-700",
    symbol: "i"
  }
}


function StatusMessage({
  type = "info",
  message,
  title = "",
  onDismiss
}) {
  if (!message) {
    return null
  }

  const style =
    MESSAGE_STYLES[type] ||
    MESSAGE_STYLES.info

  const role =
    type === "error"
      ? "alert"
      : "status"

  return (
    <div
      role={role}
      aria-live={
        type === "error"
          ? "assertive"
          : "polite"
      }
      className={`flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm ${style.container}`}
    >
      <div
        aria-hidden="true"
        className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-bold ${style.icon}`}
      >
        {style.symbol}
      </div>

      <div className="min-w-0 flex-1">
        {title && (
          <p className="font-semibold">
            {title}
          </p>
        )}

        <p
          className={
            title
              ? "mt-1 leading-5"
              : "font-medium leading-5"
          }
        >
          {message}
        </p>
      </div>

      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss message"
          className="shrink-0 rounded-lg px-2 py-1 text-sm font-bold opacity-70 transition hover:bg-black/5 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-current focus:ring-offset-2"
        >
          ×
        </button>
      )}
    </div>
  )
}


export default StatusMessage