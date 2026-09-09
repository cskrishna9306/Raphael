import { BrowserRouter, Outlet, Routes, Route } from "react-router-dom"
import { AuthProvider } from "./state/AuthContext"
import { AppStateProvider } from "./state/AppStateContext"
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

export default function App() {
  return (
    <AuthProvider>
      <AppStateProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<RequireAuth />}>
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
