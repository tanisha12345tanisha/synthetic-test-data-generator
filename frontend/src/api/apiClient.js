export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
let accessToken = null
export function setAccessToken(token) { accessToken = token }
export function getAuthHeaders(headers = {}) {
  return accessToken ? { ...headers, Authorization: `Bearer ${accessToken}` } : headers
}
export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {})
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json")
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`)
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  const data = response.headers.get("content-type")?.includes("application/json") ? await response.json() : null
  if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Request failed.")
  return data
}
