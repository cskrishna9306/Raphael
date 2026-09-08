import styles from "./ScoreBar.module.css"

interface ScoreBarProps {
  /** 0-100 fill percentage. Callers normalize their own raw score onto this scale. */
  percent: number
  label?: string
  size?: "sm" | "md"
}

export function ScoreBar({ percent, label, size = "md" }: ScoreBarProps) {
  const clamped = Math.max(0, Math.min(100, percent))
  return (
    <div className={styles.row}>
      <div className={size === "sm" ? styles.trackSm : styles.trackMd}>
        <div className={styles.fill} style={{ width: `${clamped}%` }} />
      </div>
      {label !== undefined ? <span className={styles.label}>{label}</span> : null}
    </div>
  )
}
