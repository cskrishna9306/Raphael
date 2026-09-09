import { BrowserRouter, Navigate, Outlet, Routes, Route } from "react-router-dom"
import { AuthProvider } from "./state/AuthContext"
import { AppStateProvider, useAppState } from "./state/AppStateContext"
import { HistoryProvider } from "./state/HistoryContext"
import { RequireAuth } from "./components/auth/RequireAuth"
import { AppShell } from "./components/layout/AppShell"
import { LoginPage } from "./pages/LoginPage"
import { IngestPage } from "./pages/IngestPage"
import { RosterPage } from "./pages/RosterPage"
import { AboutPage } from "./pages/AboutPage"

function ShellLayout() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  )
}

/**
 * Keyed on sessionKey so that starting a new screenplay remounts the page,
 * dropping the file and stage it was holding. Navigating here from /roster
 * remounts anyway; this covers starting over while already on it.
 */
function IngestRoute() {
  const { sessionKey } = useAppState()
  return <IngestPage key={sessionKey} />
}

export default function App() {
  return (
    <AuthProvider>
      <AppStateProvider>
        <HistoryProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              {/*
                The landing page is public, and gets the shell so a signed-out
                visitor still sees the nav bar and its sign-in tab.
              */}
              <Route element={<ShellLayout />}>
                <Route path="/" element={<AboutPage />} />
                {/* Kept so existing links and bookmarks to /about still land. */}
                <Route path="/about" element={<Navigate to="/" replace />} />
              </Route>
              {/*
                The pipeline pages get their own shell BEHIND the gate. Putting
                RequireAuth inside the shell instead would render the nav,
                roadmap and history sidebar to a signed-out visitor for the
                moment before the redirect fires.
              */}
              <Route element={<RequireAuth />}>
                <Route element={<ShellLayout />}>
                  <Route path="/ingest" element={<IngestRoute />} />
                  <Route path="/roster" element={<RosterPage />} />
                </Route>
              </Route>
            </Routes>
          </BrowserRouter>
        </HistoryProvider>
      </AppStateProvider>
    </AuthProvider>
  )
}
