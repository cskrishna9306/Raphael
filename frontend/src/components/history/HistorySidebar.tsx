import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { ApiError, getProject } from "../../api/client"
import { useAppState } from "../../state/AppStateContext"
import { useAuth } from "../../state/AuthContext"
import { useHistory } from "../../state/HistoryContext"
import { clearCachedIngestFile } from "../../utils/ingestFileCache"
import { HistoryRow } from "./HistoryRow"
import styles from "./HistorySidebar.module.css"

/**
 * Scrollable list of the signed-in user's saved screenplays. Selecting one
 * pulls its breakdown and latest report into app state and jumps to whichever
 * stage that project actually reached.
 */
export function HistorySidebar() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { projects, loading, error, remove } = useHistory()
  const { projectId, setScreenplay, setReport, setProjectId, reset } = useAppState()

  const [openingId, setOpeningId] = useState<string | null>(null)
  const [confirmingId, setConfirmingId] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  function handleStartNew() {
    setActionError(null)
    // Clears the screenplay/report/project and bumps sessionKey, which
    // remounts the ingest page so a previously dropped file doesn't linger.
    reset()
    // Dropped files survive a refresh via this cache, so starting over has to
    // clear it too or the old screenplay reappears in the dropzone.
    clearCachedIngestFile()
    navigate("/ingest")
  }

  async function handleOpen(id: string) {
    setOpeningId(id)
    setActionError(null)
    try {
      const project = await getProject(id)
      setScreenplay(project.screenplay)
      setReport(project.latest_report ?? null)
      setProjectId(project.id)
      // A project with no report never made it past the breakdown, so send
      // the user back to ingest to run the casting analysis rather than to an
      // empty roster.
      navigate(project.latest_report ? "/roster" : "/ingest")
    } catch (caught) {
      setActionError(caught instanceof ApiError ? caught.message : "Could not open that screenplay.")
    } finally {
      setOpeningId(null)
    }
  }

  async function handleDelete(id: string) {
    setConfirmingId(null)
    setActionError(null)
    try {
      await remove(id)
      // Deleting whatever is currently loaded would otherwise leave the roster
      // showing a screenplay that no longer exists.
      if (id === projectId) reset()
    } catch (caught) {
      setActionError(caught instanceof ApiError ? caught.message : "Could not delete that screenplay.")
    }
  }

  return (
    <aside className={styles.sidebar} aria-label="Screenplay history">
      <div className={styles.header}>
        <span className={styles.heading}>History</span>
        {projects.length > 0 ? <span className={styles.count}>{projects.length}</span> : null}
      </div>

      <button type="button" className={styles.newScreenplay} onClick={handleStartNew} disabled={openingId !== null}>
        + New screenplay
      </button>

      <div className={styles.scroller}>
        {!user ? (
          // Signing in is optional, so this is an invitation rather than a
          // gate -- but promising to save runs we cannot save would be a lie.
          <p className={styles.note}>
            <Link to="/login" className={styles.signInLink}>
              Sign in
            </Link>{" "}
            to save your screenplays and come back to them later.
          </p>
        ) : loading ? (
          <p className={styles.note}>Loading…</p>
        ) : error ? (
          <p className={styles.error}>{error}</p>
        ) : projects.length === 0 ? (
          <p className={styles.note}>Screenplays you analyze will be saved here.</p>
        ) : (
          <ul className={styles.list}>
            {projects.map((project) => (
              <HistoryRow
                key={project.id}
                project={project}
                isActive={project.id === projectId}
                isOpening={project.id === openingId}
                isConfirmingDelete={project.id === confirmingId}
                disabled={openingId !== null}
                onOpen={() => void handleOpen(project.id)}
                onRequestDelete={() => setConfirmingId(project.id)}
                onConfirmDelete={() => void handleDelete(project.id)}
                onCancelDelete={() => setConfirmingId(null)}
              />
            ))}
          </ul>
        )}
      </div>

      {actionError ? <p className={styles.error}>{actionError}</p> : null}
    </aside>
  )
}
