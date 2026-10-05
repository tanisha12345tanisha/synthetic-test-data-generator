import { useCallback, useEffect, useMemo, useState } from "react"

import {
  loginUser,
  logoutUser,
  refreshSession,
  registerUser
} from "../api/authApi"
import { setAccessToken } from "../api/apiClient"
import { AuthContext } from "./authContext"


const REFRESH_TOKEN_KEY = "stdg_refresh_token"


export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(() =>
    Boolean(sessionStorage.getItem(REFRESH_TOKEN_KEY))
  )

  const applySession = useCallback((session) => {
    setAccessToken(session.access_token)
    sessionStorage.setItem(
      REFRESH_TOKEN_KEY,
      session.refresh_token
    )
    setUser(session.user)
  }, [])

  const clearSession = useCallback(() => {
    setAccessToken(null)
    sessionStorage.removeItem(REFRESH_TOKEN_KEY)
    setUser(null)
  }, [])

  useEffect(() => {
    const refreshToken = sessionStorage.getItem(
      REFRESH_TOKEN_KEY
    )

    if (!refreshToken) {
      return undefined
    }

    let isActive = true

    refreshSession(refreshToken)
      .then((session) => {
        if (isActive) {
          applySession(session)
        }
      })
      .catch(() => {
        if (isActive) {
          clearSession()
        }
      })
      .finally(() => {
        if (isActive) {
          setLoading(false)
        }
      })

    return () => {
      isActive = false
    }
  }, [applySession, clearSession])

  const login = useCallback(
    async (values) => {
      const session = await loginUser(values)
      applySession(session)
    },
    [applySession]
  )

  const register = useCallback(
    async (values) => {
      const session = await registerUser(values)
      applySession(session)
    },
    [applySession]
  )

  const logout = useCallback(async () => {
    const refreshToken = sessionStorage.getItem(
      REFRESH_TOKEN_KEY
    )

    try {
      if (refreshToken) {
        await logoutUser(refreshToken)
      }
    } finally {
      clearSession()
    }
  }, [clearSession])

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      register,
      logout
    }),
    [user, loading, login, register, logout]
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
