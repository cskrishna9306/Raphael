import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AppStateProvider } from "./state/AppStateContext"
import { AppShell } from "./components/layout/AppShell"
import { IngestPage } from "./pages/IngestPage"
import { RosterPage } from "./pages/RosterPage"
import { CastingSheetPage } from "./pages/CastingSheetPage"
import { AboutPage } from "./pages/AboutPage"

export default function App() {
  return (
    <AppStateProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<IngestPage />} />
            <Route path="/roster" element={<RosterPage />} />
            <Route path="/casting-sheet" element={<CastingSheetPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </AppStateProvider>
  )
}
