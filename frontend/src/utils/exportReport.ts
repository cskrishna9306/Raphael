import type { RecommendationReport } from "../api/types"

/** Client-side only -- saves the already-fetched report, no extra API call. */
export function downloadReportAsJson(report: RecommendationReport): void {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  const safeTitle = (report.title ?? "casting-sheet").toLowerCase().replace(/[^a-z0-9]+/g, "-")
  link.href = url
  link.download = `${safeTitle}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
