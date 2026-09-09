import type { RolePresence, Screenplay } from "../../api/types"
import { toDisplayTitle } from "../../utils/format"
import styles from "./BreakdownSummary.module.css"

const ROLE_ORDER: RolePresence[] = ["lead", "supporting", "minor", "background", "extra"]

const ROLE_LABEL: Record<RolePresence, string> = {
  lead: "Lead",
  supporting: "Supporting",
  minor: "Minor",
  background: "Background",
  extra: "Extra",
}

/**
 * Standing summary of the breakdown, filling the column that previously held a
 * label and nothing else. Everything here is derived from the Screenplay
 * already in memory, so it survives loading a project from history (where no
 * File object exists).
 */
export function BreakdownSummary({ screenplay }: { screenplay: Screenplay }) {
  const characters = screenplay.cast.characters
  const total = characters.length

  const counts = ROLE_ORDER.map((role) => ({
    role,
    count: characters.filter((character) => character.role_presence === role).length,
  })).filter((entry) => entry.count > 0)

  const castDirectly = characters.filter((character) => character.preferred_actor).length

  return (
    <div className={styles.summary}>
      <div className={styles.titleBlock}>
        <div className={styles.label}>Screenplay</div>
        <h2 className={styles.title}>{toDisplayTitle(screenplay.title)}</h2>
      </div>

      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={`${styles.statValue} tabular`}>{total}</span>
          <span className={styles.statLabel}>{total === 1 ? "character" : "characters"}</span>
        </div>
        <div className={styles.stat}>
          <span className={`${styles.statValue} tabular`}>{counts.find((c) => c.role === "lead")?.count ?? 0}</span>
          <span className={styles.statLabel}>leads</span>
        </div>
        <div className={styles.stat}>
          <span className={`${styles.statValue} tabular`}>{castDirectly}</span>
          <span className={styles.statLabel}>cast directly</span>
        </div>
      </div>

      <div className={styles.block}>
        <div className={styles.label}>Role distribution</div>
        {/* One bar to the scale of the whole cast, so the shape of the
            breakdown reads before any of the numbers do. */}
        <div className={styles.bar} role="img" aria-label={counts.map((c) => `${c.count} ${ROLE_LABEL[c.role]}`).join(", ")}>
          {counts.map((entry) => (
            <div
              key={entry.role}
              className={styles[entry.role]}
              style={{ width: `${(entry.count / total) * 100}%` }}
            />
          ))}
        </div>
        <ul className={styles.legend}>
          {counts.map((entry) => (
            <li key={entry.role} className={styles.legendItem}>
              <span className={`${styles.swatch} ${styles[entry.role]}`} aria-hidden="true" />
              <span className={styles.legendLabel}>{ROLE_LABEL[entry.role]}</span>
              <span className={`${styles.legendCount} tabular`}>{entry.count}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
