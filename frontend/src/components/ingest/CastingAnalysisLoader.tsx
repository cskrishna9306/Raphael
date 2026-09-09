import { useEffect, useState } from "react"
import styles from "./CastingAnalysisLoader.module.css"

const STATUS_MESSAGES = ["Assembling candidate casts…", "Scoring ensemble chemistry…", "Flagging reputational risk…"]

/** Stand-in for the "run casting analysis" button while POST /recommend is in flight. */
export function CastingAnalysisLoader() {
  const [messageIndex, setMessageIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((index) => (index + 1) % STATUS_MESSAGES.length)
    }, 1800)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className={styles.loader}>
      <div className={styles.track}>
        <div className={styles.sweep} />
      </div>
      <div className={styles.statusRow}>
        <span className={styles.pulseDot} />
        {STATUS_MESSAGES[messageIndex]}
      </div>
    </div>
  )
}
