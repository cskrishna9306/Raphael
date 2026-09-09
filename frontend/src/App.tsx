import { BrowserRouter, Navigate, Outlet, Routes, Route } from "react-router-dom"
import { AuthProvider } from "./state/AuthContext"
import { AppStateProvider, useAppState } from "./state/AppStateContext"
import { HistoryProvider } from "./state/HistoryContext"
import { AuthGate } from "./components/auth/AuthGate"
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
                The landing page is ungated: someone should be able to read what
                Raphael does before being asked to sign in, and the nav bar's
                sign-in tab is right there when they want it.
              */}
              <Route element={<ShellLayout />}>
                <Route path="/" element={<AboutPage />} />
                {/* Kept so existing links and bookmarks to /about still land. */}
                <Route path="/about" element={<Navigate to="/" replace />} />
              </Route>
              {/*
                The pipeline pages sit behind AuthGate, which prompts for
                sign-in but lets anyone through once they sign in or skip --
                signing in is optional (see src/raphael/auth.py's
                optional_claims). The gate wraps the shell rather than sitting
                inside it, so the nav, roadmap and history rail never flash up
                for a visitor who is about to be redirected.
              */}
              <Route element={<AuthGate />}>
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
