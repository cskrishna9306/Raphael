import { BrowserRouter, Outlet, Routes, Route } from "react-router-dom"
import { AuthProvider } from "./state/AuthContext"
import { AppStateProvider } from "./state/AppStateContext"
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

// Signing in is optional (see src/raphael/auth.py's optional_claims), but the
// sign-in page is still the first thing a fresh session sees -- AuthGate lets
// anyone through once they've either signed in or explicitly skipped (see
// LoginPage). After that, NavBar's "Sign in" link is the way back to /login.
export default function App() {
  return (
    <AuthProvider>
      <AppStateProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<AuthGate />}>
              <Route element={<ShellLayout />}>
                <Route path="/" element={<IngestPage />} />
                <Route path="/roster" element={<RosterPage />} />
                <Route path="/about" element={<AboutPage />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AppStateProvider>
    </AuthProvider>
  )
}
