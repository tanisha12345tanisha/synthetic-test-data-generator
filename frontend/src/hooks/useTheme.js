import { useEffect, useState } from "react"


const THEME_STORAGE_KEY = "synthetic-data-generator-theme"

const THEME_LIGHT = "light"
const THEME_DARK = "dark"


function getInitialTheme() {
  const savedTheme =
    window.localStorage.getItem(
      THEME_STORAGE_KEY
    )

  if (
    savedTheme === THEME_LIGHT ||
    savedTheme === THEME_DARK
  ) {
    return savedTheme
  }

  const systemPrefersDark =
    window.matchMedia?.(
      "(prefers-color-scheme: dark)"
    ).matches

  return systemPrefersDark
    ? THEME_DARK
    : THEME_LIGHT
}


function applyTheme(theme) {
  const rootElement =
    document.documentElement

  rootElement.classList.toggle(
    "dark",
    theme === THEME_DARK
  )

  rootElement.dataset.theme = theme
  rootElement.style.colorScheme = theme
}


export function useTheme() {
  const [theme, setTheme] =
    useState(getInitialTheme)

  useEffect(() => {
    applyTheme(theme)

    window.localStorage.setItem(
      THEME_STORAGE_KEY,
      theme
    )
  }, [theme])

  function toggleTheme() {
    setTheme(
      (currentTheme) =>
        currentTheme === THEME_DARK
          ? THEME_LIGHT
          : THEME_DARK
    )
  }

  return {
    theme,
    isDarkMode:
      theme === THEME_DARK,
    setTheme,
    toggleTheme
  }
}