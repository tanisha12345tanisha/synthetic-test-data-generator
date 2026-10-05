import { useState } from "react"

import AppHeader from "./AppHeader"
import Sidebar from "./Sidebar"


function AppShell({
  children,
  title,
  description,
  headerActions,
  activeNavigationItem = "generator",
  isDarkMode,
  onToggleTheme,
  onSelectNavigation
}) {
  const [
    isSidebarOpen,
    setIsSidebarOpen
  ] = useState(false)

  function handleNavigation(
    navigationItem
  ) {
    onSelectNavigation?.(
      navigationItem
    )

    setIsSidebarOpen(false)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 transition-colors dark:bg-slate-950 dark:text-slate-100">
      <Sidebar
        isOpen={isSidebarOpen}
        activeItem={
          activeNavigationItem
        }
        onSelect={
          handleNavigation
        }
        onClose={() =>
          setIsSidebarOpen(false)
        }
      />

      <div className="min-h-screen lg:pl-72">
        <AppHeader
          title={title}
          description={description}
          actions={headerActions}
          isDarkMode={isDarkMode}
          onToggleTheme={
            onToggleTheme
          }
          onOpenSidebar={() =>
            setIsSidebarOpen(true)
          }
        />

        <div className="min-h-[calc(100vh-73px)]">
          {children}
        </div>
      </div>
    </div>
  )
}


export default AppShell