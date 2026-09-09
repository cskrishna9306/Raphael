import { useState, type DragEvent } from "react"
import { useNavigate } from "react-router-dom"
import { analyzeScreenplay, createProject, recommendCastStream, ApiError } from "../api/client"
import type { RolePresence } from "../api/types"
import { useAppState } from "../state/AppStateContext"
import { useHistory } from "../state/HistoryContext"
import { Panel } from "../components/common/Panel"
import { Button } from "../components/common/Button"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { FileDropzone, isAcceptedFile } from "../components/ingest/FileDropzone"
import { FileCard } from "../components/ingest/FileCard"
import { CharacterList } from "../components/ingest/CharacterList"
import { BreakdownSkeleton } from "../components/ingest/BreakdownSkeleton"
import { BreakdownSummary } from "../components/ingest/BreakdownSummary"
import { CastingAnalysisLoader } from "../components/ingest/CastingAnalysisLoader"
import { cacheIngestFile, clearCachedIngestFile, loadCachedIngestFile } from "../utils/ingestFileCache"
import styles from "./IngestPage.module.css"

type Stage = "empty" | "ready" | "analyzing" | "reviewing" | "recommending"

export function IngestPage() {
  const navigate = useNavigate()
  const { screenplay, projectId, setScreenplay, setReport, setProjectId } = useAppState()
  const { refresh: refreshHistory } = useHistory()
  // Restore a screenplay dropped before a refresh -- cacheIngestFile only ever
  // stores one while `screenplay` is unset, so it only applies to that state.
  const [file, setFile] = useState<File | null>(() => (screenplay ? null : loadCachedIngestFile()))
  const [stage, setStage] = useState<Stage>(() => {
    if (screenplay) return "reviewing"
    return file ? "ready" : "empty"
  })
  const [error, setError] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [castingProgress, setCastingProgress] = useState<{ character: string; completed: number; total: number } | null>(null)

  function handleFileSelected(nextFile: File) {
    setFile(nextFile)
    setError(null)
    setStage("ready")
    void cacheIngestFile(nextFile)
  }

  function handleClearFile() {
    setFile(null)
    clearCachedIngestFile()
  }

  function handleDropzoneDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragOver(true)
  }

  function handleDropzoneDragLeave(event: DragEvent<HTMLDivElement>) {
    if (event.currentTarget.contains(event.relatedTarget as Node)) return
    setIsDragOver(false)
  }

  function handleDropzoneDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragOver(false)
    const droppedFile = event.dataTransfer.files[0]
    if (droppedFile && isAcceptedFile(droppedFile)) handleFileSelected(droppedFile)
  }

  async function handleRunBreakdown() {
    if (!file) return
    setStage("analyzing")
    setError(null)
    try {
      const result = await analyzeScreenplay(file)
      setScreenplay(result)
      setStage("reviewing")

      // Saved as soon as the breakdown lands, so a screenplay shows up in
      // history even if the user never runs the casting analysis. Failing to
      // save must not cost them the breakdown they just waited for, so this
      // stays out of the catch below.
      try {
        const project = await createProject(result)
        setProjectId(project.id)
        await refreshHistory()
      } catch (historyError) {
        console.error("Could not save this screenplay to history", historyError)
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the Raphael API. Is the server running?")
      setStage("ready")
    }
  }

  function handleRoleChange(characterName: string, role: RolePresence) {
    if (!screenplay) return
    setScreenplay({
      ...screenplay,
      cast: {
        characters: screenplay.cast.characters.map((character) =>
          character.name === characterName ? { ...character, role_presence: role } : character,
        ),
      },
    })
  }

  function handlePreferredActorChange(characterName: string, preferredActor: string | null) {
    if (!screenplay) return
    setScreenplay({
      ...screenplay,
      cast: {
        characters: screenplay.cast.characters.map((character) =>
          character.name === characterName ? { ...character, preferred_actor: preferredActor } : character,
        ),
      },
    })
  }

  async function handleRunCastingAnalysis() {
    if (!screenplay) return
    setStage("recommending")
    setError(null)
    setCastingProgress(null)
    try {
      const result = await recommendCastStream(screenplay, setCastingProgress, projectId ?? undefined)
      setReport(result)
      // Flips this project's row to "Roster ready" and moves it to the top.
      void refreshHistory()
      navigate("/roster")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the Raphael API. Is the server running?")
      setStage("reviewing")
    }
  }

  const isBusy = stage === "analyzing" || stage === "recommending"

  return (
    <div className={styles.page}>
      <Panel className={styles.panel}>
        {!screenplay && stage !== "analyzing" ? (
          <div
            className={styles.emptyState}
            onDragOver={handleDropzoneDragOver}
            onDragLeave={handleDropzoneDragLeave}
            onDrop={handleDropzoneDrop}
          >
            <div className={styles.heading}>
              <div className={styles.headline}>Every cast starts with a page</div>
              <div className={styles.subhead}>Drop your screenplay below and Raphael will analyze it!</div>
            </div>
            <FileDropzone onFileSelected={handleFileSelected} isDragOver={isDragOver} />
            {file ? (
              <div className={styles.readyRow}>
                <FileCard file={file} status="uploaded" onReplace={handleClearFile} />
              </div>
            ) : null}
            <Button variant={file ? "primary" : "secondary"} disabled={!file} onClick={handleRunBreakdown}>
              Run screenplay breakdown →
            </Button>
            <div className={styles.hint}>Reads scenes, roles and screen time.</div>
          </div>
        ) : (
          <div className={styles.splitView}>
            <div className={styles.leftColumn}>
              {screenplay ? <BreakdownSummary screenplay={screenplay} /> : null}
              {file ? (
                <FileCard
                  file={file}
                  status={stage === "analyzing" ? "reading" : "uploaded"}
                  onReplace={() => {
                    handleClearFile()
                    setScreenplay(null)
                    setReport(null)
                    // Detach from the saved project rather than deleting it --
                    // it stays in history, this is just a fresh run.
                    setProjectId(null)
                    setStage("empty")
                  }}
                  replaceDisabled={isBusy}
                />
              ) : null}
              {screenplay && stage !== "analyzing" ? (
                // The action lives beside the summary rather than under the
                // cast list, so it stays reachable however long the list runs.
                <div className={styles.actionBlock}>
                  <div className={styles.statusRow}>
                    <span className={styles.statusDot} />
                    Breakdown complete
                  </div>
                  {stage === "recommending" ? (
                    <CastingAnalysisLoader progress={castingProgress} />
                  ) : (
                    <Button
                      variant="primary"
                      disabled={isBusy || screenplay.cast.characters.length === 0}
                      onClick={handleRunCastingAnalysis}
                    >
                      Run casting analysis →
                    </Button>
                  )}
                </div>
              ) : null}
            </div>
            <div className={styles.rightColumn}>
              {stage === "analyzing" || !screenplay ? (
                <BreakdownSkeleton />
              ) : (
                <>
                  <div className={styles.charactersHeader}>
                    <span className={styles.sectionLabel}>Characters detected</span>
                    <span className={styles.charactersHint}>Set a role, or cast an actor directly</span>
                  </div>
                  <CharacterList
                    characters={screenplay.cast.characters}
                    onRoleChange={handleRoleChange}
                    onPreferredActorChange={handlePreferredActorChange}
                    disabled={isBusy}
                  />
                </>
              )}
            </div>
          </div>
        )}
      </Panel>
      {error ? <ErrorBanner message={error} /> : null}
    </div>
  )
}
