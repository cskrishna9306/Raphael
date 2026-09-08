import type { BackendStatus } from "../../hooks/useBackendStatus"
import styles from "./StatusBanner.module.css"

export function StatusBanner({ status }: { status: BackendStatus }) {
  if (status !== "offline") return null

  return (
    <div className={styles.banner} role="alert">
      <span className={styles.dot} aria-hidden="true" />
      Raphael's backend isn't responding (health/ready checks failed) -- start it with{" "}
      <code className={styles.code}>uv run python -m src.raphael.main</code> from the repo root.
    </div>
  )
}
