import { apiRequest } from "./apiClient"
const json = (body) => ({ method: "POST", body: JSON.stringify(body) })
export const registerUser = (body) => apiRequest("/auth/register", json(body))
export const loginUser = (body) => apiRequest("/auth/login", json(body))
export const refreshSession = (refresh_token) => apiRequest("/auth/refresh", json({ refresh_token }))
export const logoutUser = (refresh_token) => apiRequest("/auth/logout", json({ refresh_token }))
export const getCurrentUser = () => apiRequest("/auth/me")
export const forgotPassword = (email) => apiRequest("/auth/forgot-password", json({ email }))
export const resetPassword = (body) => apiRequest("/auth/reset-password", json(body))
