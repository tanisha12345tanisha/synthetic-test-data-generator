import { useState } from "react"
import { forgotPassword, resetPassword } from "../api/authApi"
import { useAuth } from "../context/authContext"

const inputClass = "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none focus:border-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
export default function AuthPage() {
  const { login, register } = useAuth()
  const token = new URLSearchParams(window.location.search).get("token")
  const [mode, setMode] = useState(token ? "reset" : "login")
  const [form, setForm] = useState({ display_name: "", email: "", password: "", confirm_password: "", token: token || "" })
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const change = (e) => setForm((v) => ({ ...v, [e.target.name]: e.target.value }))
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError(""); setMessage("")
    try {
      if (mode === "login") await login({ email: form.email, password: form.password })
      if (mode === "register") await register(form)
      if (mode === "forgot") { const r = await forgotPassword(form.email); setMessage(r.message) }
      if (mode === "reset") { const r = await resetPassword({ token: form.token, password: form.password, confirm_password: form.confirm_password }); setMessage(r.message); setMode("login") }
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  return <main className="min-h-screen bg-slate-100 p-6 dark:bg-slate-950">
    <div className="mx-auto mt-12 max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-800 dark:bg-slate-900">
      <p className="text-sm font-semibold uppercase tracking-widest text-blue-600">Synthetic Test Data Generator</p>
      <h1 className="mt-3 text-3xl font-bold text-slate-950 dark:text-white">{mode === "register" ? "Create account" : mode === "forgot" ? "Reset password" : mode === "reset" ? "Choose new password" : "Welcome back"}</h1>
      <form className="mt-8 space-y-4" onSubmit={submit}>
        {mode === "register" && <input className={inputClass} name="display_name" placeholder="Display name" value={form.display_name} onChange={change} required />}
        {mode !== "reset" && <input className={inputClass} name="email" type="email" placeholder="Email" value={form.email} onChange={change} required />}
        {(mode === "login" || mode === "register" || mode === "reset") && <input className={inputClass} name="password" type="password" placeholder="Password" value={form.password} onChange={change} required />}
        {(mode === "register" || mode === "reset") && <input className={inputClass} name="confirm_password" type="password" placeholder="Confirm password" value={form.confirm_password} onChange={change} required />}
        {error && <p className="text-sm text-red-600">{error}</p>}{message && <p className="text-sm text-green-600">{message}</p>}
        <button disabled={busy} className="w-full rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white disabled:opacity-60">{busy ? "Working..." : "Continue"}</button>
      </form>
      <div className="mt-6 flex flex-wrap gap-3 text-sm text-blue-600">
        {mode !== "login" && <button onClick={() => setMode("login")}>Sign in</button>}
        {mode !== "register" && <button onClick={() => setMode("register")}>Create account</button>}
        {mode === "login" && <button onClick={() => setMode("forgot")}>Forgot password?</button>}
      </div>
    </div>
  </main>
}
