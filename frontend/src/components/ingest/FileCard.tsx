import styles from "./FileCard.module.css"

function formatSize(bytes: number): string {
  const mb = bytes / (1024 * 1024)
  if (mb >= 0.1) return `${mb.toFixed(1)} MB`
  return `${Math.max(1, Math.round(bytes / 1024))} KB`
}

interface FileCardProps {
  file: File
  status: string
  onReplace: () => void
  replaceDisabled?: boolean
}

export function FileCard({ file, status, onReplace, replaceDisabled }: FileCardProps) {
  return (
    <div className={styles.card}>
      <div className={styles.icon} aria-hidden="true" />
      <div className={styles.meta}>
        <div className={styles.name}>{file.name}</div>
        <div className={styles.status}>
          {formatSize(file.size)} · {status}
        </div>
      </div>
      <button type="button" className={styles.replace} onClick={onReplace} disabled={replaceDisabled}>
        Replace
      </button>
    </div>
  )
}
