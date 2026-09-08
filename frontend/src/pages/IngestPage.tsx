import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { analyzeScreenplay, recommendCast, ApiError } from "../api/client"
import type { RolePresence } from "../api/types"
import { useAppState } from "../state/AppStateContext"
import { Panel } from "../components/common/Panel"
import { Button } from "../components/common/Button"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { FileDropzone } from "../components/ingest/FileDropzone"
import { FileCard } from "../components/ingest/FileCard"
import { CharacterList } from "../components/ingest/CharacterList"
import { BreakdownSkeleton } from "../components/ingest/BreakdownSkeleton"
import styles from "./IngestPage.module.css"

type Stage = "empty" | "ready" | "analyzing" | "reviewing" | "recommending"

export function IngestPage() {
  const navigate = useNavigate()
  const { screenplay, setScreenplay, setReport } = useAppState()
  const [stage, setStage] = useState<Stage>(screenplay ? "reviewing" : "empty")
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  function handleFileSelected(nextFile: File) {
    setFile(nextFile)
    setError(null)
    setStage("ready")
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
          <div className={styles.emptyState}>
            <div className={styles.heading}>
              <div className={styles.headline}>Every cast starts with a page</div>
              <div className={styles.subhead}>Drop your screenplay below and Raphael will analyze it!</div>
            </div>
            <FileDropzone onFileSelected={handleFileSelected} />
            {file ? (
              <div className={styles.readyRow}>
                <FileCard file={file} status="uploaded" onReplace={() => setFile(null)} />
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
                    setFile(null)
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
                    <span className={styles.charactersHint}>edit a row's role before casting</span>
                  </div>
                  <CharacterList
                    characters={screenplay.cast.characters}
                    onRoleChange={handleRoleChange}
                    disabled={isBusy}
                  />
                  <Button
                    variant="primary"
                    disabled={isBusy || screenplay.cast.characters.length === 0}
                    onClick={handleRunCastingAnalysis}
                  >
                    {stage === "recommending" ? "RUNNING CASTING ANALYSIS…" : "RUN CASTING ANALYSIS →"}
                  </Button>
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
