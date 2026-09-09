import { useEffect, useState } from "react"
import styles from "./CastingAnalysisLoader.module.css"

// casting_director's per-character progress (see CastingProgress below) covers the search
// phase for real; there's no equivalent per-item signal yet for chemistry/risk scoring, so
// once casting hits 100% this cycles an honest "still working" message rather than pretending
// to track those steps too.
const POST_CASTING_MESSAGES = ["Scoring ensemble chemistry…", "Flagging reputational risk…"]

export interface CastingProgress {
  character: string
  completed: number
  total: number
}

/** Shown while POST /recommend/stream is in flight -- real per-character casting progress, then an honest fallback for the remaining un-instrumented steps. */
export function CastingAnalysisLoader({ progress }: { progress: CastingProgress | null }) {
  const [messageIndex, setMessageIndex] = useState(0)
  const castingDone = progress !== null && progress.completed >= progress.total

  useEffect(() => {
    if (!castingDone) return
    const interval = setInterval(() => {
      setMessageIndex((index) => (index + 1) % POST_CASTING_MESSAGES.length)
    }, 1800)
    return () => clearInterval(interval)
  }, [castingDone])

  const percent = progress ? Math.min(100, Math.round((progress.completed / progress.total) * 100)) : 0

  return (
    <div className={styles.loader}>
      <div className={styles.track}>
        <div className={styles.fill} style={{ width: `${castingDone ? 100 : percent}%` }} />
      </div>
      <div className={styles.statusRow}>
        <span className={styles.pulseDot} />
        {!progress
          ? "Assembling candidate casts…"
          : castingDone
            ? POST_CASTING_MESSAGES[messageIndex]
            : `Cast "${progress.character}" · ${progress.completed}/${progress.total} characters`}
      </div>
    </div>
  )
}
