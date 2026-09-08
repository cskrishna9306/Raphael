import { useEffect, useState } from "react"
import { checkBackendStatus } from "../api/client"

export type BackendStatus = "checking" | "online" | "offline"

const POLL_INTERVAL_MS = 15000

/** Polls /health + /ready on an interval so the shell can show a banner when the backend drops. */
export function useBackendStatus(): BackendStatus {
  const [status, setStatus] = useState<BackendStatus>("checking")

  useEffect(() => {
    let cancelled = false

    async function poll() {
      const isUp = await checkBackendStatus()
      if (!cancelled) setStatus(isUp ? "online" : "offline")
    }

    poll()
    const intervalId = setInterval(poll, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(intervalId)
    }
  }, [])

  return status
}
