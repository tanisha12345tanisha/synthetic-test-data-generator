import { apiRequest } from "./apiClient"
const json = (method, body) => ({ method, body: JSON.stringify(body) })
export const getAdminSummary = () => apiRequest("/admin/summary")
export const listAdminUsers = () => apiRequest("/admin/users")
export const updateAdminUser = (id, body) => apiRequest(`/admin/users/${id}`, json("PATCH", body))
export const listSystemLimits = () => apiRequest("/admin/limits")
export const setSystemLimit = (key, value, unit = null) => apiRequest(`/admin/limits/${key}`, json("PUT", { key, value, unit }))
export const listAuditEvents = () => apiRequest("/admin/audit-events?limit=100")
