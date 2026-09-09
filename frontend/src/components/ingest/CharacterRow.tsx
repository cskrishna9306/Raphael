import { useState } from "react"
import type { CharacterProfile, RolePresence } from "../../api/types"
import { toDisplayName } from "../../utils/format"
import styles from "./CharacterRow.module.css"

// The three weights a director actually re-assigns. background/extra are still
// valid API values and are preserved when present, but they aren't offered as
// choices -- CastingDirectorAgent excludes them from casting anyway.
const ROLE_OPTIONS: RolePresence[] = ["lead", "supporting", "minor"]

const ROLE_LABEL: Record<RolePresence, string> = {
  lead: "Lead",
  supporting: "Supporting",
  minor: "Minor",
  background: "Background",
  extra: "Extra",
}

interface CharacterRowProps {
  character: CharacterProfile
  onRoleChange: (role: RolePresence) => void
  onPreferredActorChange: (value: string | null) => void
  disabled?: boolean
}

export function CharacterRow({ character, onRoleChange, onPreferredActorChange, disabled }: CharacterRowProps) {
  const isLead = character.role_presence === "lead"
  const [isEditingActor, setIsEditingActor] = useState(false)
  const [draftActor, setDraftActor] = useState(character.preferred_actor ?? "")

  // A role the segmented control can't represent (background/extra) still has
  // to be visible, so it gets shown as a fourth, already-selected option.
  const options: RolePresence[] = ROLE_OPTIONS.includes(character.role_presence)
    ? ROLE_OPTIONS
    : [...ROLE_OPTIONS, character.role_presence]

  function startEditing() {
    setDraftActor(character.preferred_actor ?? "")
    setIsEditingActor(true)
  }

  function commitActor() {
    const trimmed = draftActor.trim()
    onPreferredActorChange(trimmed || null)
    setIsEditingActor(false)
  }

  function cancelEditing() {
    setDraftActor(character.preferred_actor ?? "")
    setIsEditingActor(false)
  }

  return (
    <div className={[styles.row, isLead ? styles.rowLead : ""].join(" ")}>
      <div className={styles.head}>
        <div className={styles.identity}>
          <div className={styles.name}>{toDisplayName(character.name)}</div>
          {character.description ? <div className={styles.description}>{character.description}</div> : null}
        </div>

        {/* Replaces a native <select>: shows every choice at once, takes one
            click instead of two, and carries no OS chrome. */}
        <div className={styles.roles} role="radiogroup" aria-label={`Role for ${toDisplayName(character.name)}`}>
          {options.map((role) => {
            const isSelected = role === character.role_presence
            return (
              <button
                key={role}
                type="button"
                role="radio"
                aria-checked={isSelected}
                disabled={disabled}
                className={isSelected ? styles.roleSelected : styles.role}
                onClick={() => onRoleChange(role)}
              >
                {ROLE_LABEL[role]}
              </button>
            )
          })}
        </div>
      </div>

      <div className={styles.footRow}>
        {character.traits && character.traits.length > 0 ? (
          <div className={styles.traits}>
            {character.traits.slice(0, 3).map((trait) => (
              <span key={trait} className={styles.trait}>
                {trait}
              </span>
            ))}
          </div>
        ) : (
          <span />
        )}

        {isEditingActor ? (
          <input
            className={styles.actorInput}
            type="text"
            value={draftActor}
            disabled={disabled}
            autoFocus
            placeholder="Cast a specific actor…"
            aria-label={`Preferred actor for ${toDisplayName(character.name)}`}
            onChange={(event) => setDraftActor(event.target.value)}
            onBlur={commitActor}
            onKeyDown={(event) => {
              if (event.key === "Enter") commitActor()
              if (event.key === "Escape") cancelEditing()
            }}
          />
        ) : (
          <button type="button" className={styles.actorToggle} disabled={disabled} onClick={startEditing}>
            {character.preferred_actor ? (
              <span className={styles.actorChosen}>{character.preferred_actor}</span>
            ) : (
              <span className={styles.actorPlaceholder}>Cast directly</span>
            )}
          </button>
        )}
      </div>
    </div>
  )
}
