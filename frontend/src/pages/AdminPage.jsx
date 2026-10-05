import { useEffect, useState } from "react"

import {
  getAdminSummary,
  listAdminUsers,
  listAuditEvents,
  listSystemLimits,
  setSystemLimit,
  updateAdminUser
} from "../api/adminApi"


const CARD_CLASS =
  "rounded-2xl border border-slate-200 bg-white p-5 shadow-sm " +
  "dark:border-slate-800 dark:bg-slate-900 dark:text-white"


function parseLimitValue(rawValue) {
  try {
    return JSON.parse(rawValue)
  } catch {
    const numericValue = Number(rawValue)

    return Number.isNaN(numericValue)
      ? rawValue
      : numericValue
  }
}


export default function AdminPage({ onClose }) {
  const [summary, setSummary] = useState(null)
  const [users, setUsers] = useState([])
  const [limits, setLimits] = useState([])
  const [events, setEvents] = useState([])
  const [error, setError] = useState("")

  async function loadAdminData() {
    setError("")

    try {
      const [
        summaryResult,
        usersResult,
        limitsResult,
        eventsResult
      ] = await Promise.all([
        getAdminSummary(),
        listAdminUsers(),
        listSystemLimits(),
        listAuditEvents()
      ])

      setSummary(summaryResult)
      setUsers(usersResult)
      setLimits(limitsResult)
      setEvents(eventsResult)
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Failed to load admin data."
      )
    }
  }

  useEffect(() => {
    let isActive = true

    Promise.all([
      getAdminSummary(),
      listAdminUsers(),
      listSystemLimits(),
      listAuditEvents()
    ])
      .then(
        ([
          summaryResult,
          usersResult,
          limitsResult,
          eventsResult
        ]) => {
          if (!isActive) {
            return
          }

          setSummary(summaryResult)
          setUsers(usersResult)
          setLimits(limitsResult)
          setEvents(eventsResult)
        }
      )
      .catch((loadError) => {
        if (!isActive) {
          return
        }

        setError(
          loadError instanceof Error
            ? loadError.message
            : "Failed to load admin data."
        )
      })

    return () => {
      isActive = false
    }
  }, [])

  async function changeUser(user, field, value) {
    setError("")

    try {
      await updateAdminUser(
        user.id,
        {
          value
        }
      )

      await loadAdminData()
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "Failed to update the user."
      )
    }
  }

  async function editLimit(limit) {
    const rawValue = window.prompt(
      `New value for ${limit.key}`,
      typeof limit.value === "object"
        ? JSON.stringify(limit.value)
        : String(limit.value)
    )

    if (rawValue === null) {
      return
    }

    setError("")

    try {
      await setSystemLimit(
        limit.key,
        parseLimitValue(rawValue),
        limit.unit
      )

      await loadAdminData()
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "Failed to update the system limit."
      )
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 p-6 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-3xl font-bold text-slate-950 dark:text-white">
            Admin portal
          </h1>

          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-slate-900 px-4 py-2 font-semibold text-white dark:bg-white dark:text-slate-900"
          >
            Back
          </button>
        </div>

        {error && (
          <div
            role="alert"
            className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300"
          >
            {error}
          </div>
        )}

        {summary && (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(summary).map(([key, value]) => (
              <div
                key={key}
                className={CARD_CLASS}
              >
                <p className="text-sm capitalize text-slate-500 dark:text-slate-400">
                  {key.replaceAll("_", " ")}
                </p>

                <p className="mt-2 text-3xl font-bold">
                  {value}
                </p>
              </div>
            ))}
          </div>
        )}

        <section className={`${CARD_CLASS} mt-6`}>
          <h2 className="text-xl font-bold">
            Users
          </h2>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="p-3">
                    User
                  </th>

                  <th className="p-3">
                    Role
                  </th>

                  <th className="p-3">
                    Status
                  </th>
                </tr>
              </thead>

              <tbody>
                {users.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-slate-100 dark:border-slate-800"
                  >
                    <td className="p-3">
                      <p className="font-medium">
                        {user.display_name}
                      </p>

                      <p className="text-slate-500 dark:text-slate-400">
                        {user.email}
                      </p>
                    </td>

                    <td className="p-3">
                      <select
                        aria-label={`Role for ${user.email}`}
                        value={user.role}
                        onChange={(event) =>
                          changeUser(
                            user,
                            "role",
                            event.target.value
                          )
                        }
                        className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                      >
                        <option value="user">
                          User
                        </option>

                        <option value="admin">
                          Admin
                        </option>
                      </select>
                    </td>

                    <td className="p-3">
                      <select
                        aria-label={`Status for ${user.email}`}
                        value={user.status}
                        onChange={(event) =>
                          changeUser(
                            user,
                            "status",
                            event.target.value
                          )
                        }
                        className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                      >
                        <option value="active">
                          Active
                        </option>

                        <option value="disabled">
                          Disabled
                        </option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {users.length === 0 && (
              <p className="py-8 text-center text-slate-500 dark:text-slate-400">
                No users found.
              </p>
            )}
          </div>
        </section>

        <section className={`${CARD_CLASS} mt-6`}>
          <h2 className="text-xl font-bold">
            System controls
          </h2>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {limits.map((limit) => (
              <button
                key={limit.id}
                type="button"
                onClick={() => editLimit(limit)}
                className="rounded-xl border border-slate-200 p-4 text-left transition hover:border-blue-500 hover:bg-blue-50 dark:border-slate-700 dark:hover:border-blue-500 dark:hover:bg-blue-950/30"
              >
                <span className="font-semibold">
                  {limit.key}
                </span>

                <span className="mt-1 block text-slate-500 dark:text-slate-400">
                  {JSON.stringify(limit.value)}
                  {limit.unit
                    ? ` ${limit.unit}`
                    : ""}
                </span>
              </button>
            ))}
          </div>

          {limits.length === 0 && (
            <p className="mt-4 text-slate-500 dark:text-slate-400">
              No system controls are available.
            </p>
          )}
        </section>

        <section className={`${CARD_CLASS} mt-6`}>
          <h2 className="text-xl font-bold">
            Audit events
          </h2>

          <div className="mt-4 max-h-96 space-y-2 overflow-auto">
            {events.map((event) => (
              <article
                key={event.id}
                className="rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-700"
              >
                <p className="font-semibold">
                  {event.action}
                </p>

                <p className="mt-1 text-slate-500 dark:text-slate-400">
                  {event.result}
                  {" · "}
                  {new Date(
                    event.timestamp
                  ).toLocaleString()}
                </p>
              </article>
            ))}
          </div>

          {events.length === 0 && (
            <p className="mt-4 text-slate-500 dark:text-slate-400">
              No audit events are available.
            </p>
          )}
        </section>
      </div>
    </main>
  )
}