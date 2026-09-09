import { useState, type DragEvent } from "react"
import { useNavigate } from "react-router-dom"
import { analyzeScreenplay, recommendCast, ApiError } from "../api/client"
import type { RolePresence } from "../api/types"
import { useAppState } from "../state/AppStateContext"
import { Panel } from "../components/common/Panel"
import { Button } from "../components/common/Button"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { FileDropzone, isAcceptedFile } from "../components/ingest/FileDropzone"
import { FileCard } from "../components/ingest/FileCard"
import { CharacterList } from "../components/ingest/CharacterList"
import { BreakdownSkeleton } from "../components/ingest/BreakdownSkeleton"
import { CastingAnalysisLoader } from "../components/ingest/CastingAnalysisLoader"
import { cacheIngestFile, clearCachedIngestFile, loadCachedIngestFile } from "../utils/ingestFileCache"
import styles from "./IngestPage.module.css"

type Stage = "empty" | "ready" | "analyzing" | "reviewing" | "recommending"

export function IngestPage() {
  const navigate = useNavigate()
  const { screenplay, setScreenplay, setReport } = useAppState()
  // Restore a screenplay dropped before a refresh -- cacheIngestFile only ever
  // stores one while `screenplay` is unset, so it only applies to that state.
  const [file, setFile] = useState<File | null>(() => (screenplay ? null : loadCachedIngestFile()))
  const [stage, setStage] = useState<Stage>(() => {
    if (screenplay) return "reviewing"
    return file ? "ready" : "empty"
  })
  const [error, setError] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)

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
    try {
      const result = await recommendCast(screenplay)
      setReport(result)
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
              RUN SCREENPLAY BREAKDOWN →
            </Button>
            <div className={styles.hint}>Reads scenes, roles and screen time.</div>
          </div>
        ) : (
          <div className={styles.splitView}>
            <div className={styles.leftColumn}>
              <div className={styles.sectionLabel}>Screenplay</div>
              {file ? (
                <FileCard
                  file={file}
                  status={stage === "analyzing" ? "reading" : "uploaded"}
                  onReplace={() => {
                    handleClearFile()
                    setScreenplay(null)
                    setReport(null)
                    setStage("empty")
                  }}
                  replaceDisabled={isBusy}
                />
              ) : null}
              {stage !== "analyzing" ? (
                <div className={styles.statusRow}>
                  <span className={styles.statusDot} />
                  Breakdown complete{screenplay ? ` · ${screenplay.cast.characters.length} characters` : ""}
                </div>
              ) : null}
            </div>
            <div className={styles.rightColumn}>
              <div className={styles.sectionLabel}>Breakdown</div>
              {stage === "analyzing" || !screenplay ? (
                <BreakdownSkeleton />
              ) : (
                <>
                  <div className={styles.summaryCard}>
                    <div className={styles.summaryTitleRow}>
                      <div className={styles.summaryTitle}>{screenplay.title}</div>
                    </div>
                  </div>
                  <div className={styles.charactersHeader}>
                    <span>Characters detected — {screenplay.cast.characters.length}</span>
                    <span className={styles.charactersHint}>edit a role or cast a specific actor before casting</span>
                  </div>
                  <CharacterList
                    characters={screenplay.cast.characters}
                    onRoleChange={handleRoleChange}
                    onPreferredActorChange={handlePreferredActorChange}
                    disabled={isBusy}
                  />
                  {stage === "recommending" ? (
                    <CastingAnalysisLoader />
                  ) : (
                    <Button
                      variant="primary"
                      disabled={isBusy || screenplay.cast.characters.length === 0}
                      onClick={handleRunCastingAnalysis}
                    >
                      RUN CASTING ANALYSIS →
                    </Button>
                  )}
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
