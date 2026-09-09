import type { ProjectSummary } from "../../api/types"
import { formatRelativeTime } from "../../utils/format"
import styles from "./HistoryRow.module.css"

interface HistoryRowProps {
  project: ProjectSummary
  isActive: boolean
  isOpening: boolean
  isConfirmingDelete: boolean
  disabled: boolean
  onOpen: () => void
  onRequestDelete: () => void
  onConfirmDelete: () => void
  onCancelDelete: () => void
}

export function HistoryRow({
  project,
  isActive,
  isOpening,
  isConfirmingDelete,
  disabled,
  onOpen,
  onRequestDelete,
  onConfirmDelete,
  onCancelDelete,
}: HistoryRowProps) {
  const timestamp = formatRelativeTime(project.updated_at ?? project.created_at)

  const classNames = [styles.row, isActive ? styles.rowActive : "", isOpening ? styles.rowOpening : ""]

  return (
    <li className={classNames.filter(Boolean).join(" ")}>
      <button
        type="button"
        className={styles.open}
        onClick={onOpen}
        disabled={disabled}
        aria-current={isActive ? "true" : undefined}
      >
        <span className={styles.title}>{project.title}</span>
        <span className={styles.meta}>
          <span>
            {project.character_count} {project.character_count === 1 ? "character" : "characters"}
          </span>
          {timestamp ? <span className={styles.timestamp}>{timestamp}</span> : null}
        </span>
        <span className={project.has_report ? styles.badgeReady : styles.badgePending}>
          {project.has_report ? "Roster ready" : "Breakdown only"}
        </span>
      </button>

      {isConfirmingDelete ? (
        // Two-step rather than a window.confirm: the deletion takes the
        // report with it on the server and there is no undo.
        <div className={styles.confirm}>
          <button type="button" className={styles.confirmDelete} onClick={onConfirmDelete}>
            Delete
          </button>
          <button type="button" className={styles.confirmCancel} onClick={onCancelDelete}>
            Cancel
          </button>
        </div>
      ) : (
        <button
          type="button"
          className={styles.delete}
          onClick={onRequestDelete}
          disabled={disabled}
          aria-label={`Delete ${project.title}`}
          title="Delete"
        >
          ×
        </button>
      )}
    </li>
  )
}
