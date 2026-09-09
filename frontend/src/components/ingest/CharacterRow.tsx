import { useState } from "react"
import type { CharacterProfile, RolePresence } from "../../api/types"
import styles from "./CharacterRow.module.css"

const ROLE_OPTIONS: RolePresence[] = ["lead", "supporting", "minor", "background", "extra"]

const ROLE_LABEL: Record<RolePresence, string> = {
  lead: "LEAD",
  supporting: "SUPP",
  minor: "MINOR",
  background: "BG",
  extra: "EXTRA",
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
      <div className={styles.mainLine}>
        <select
          className={styles.roleSelect}
          value={character.role_presence}
          disabled={disabled}
          onChange={(event) => onRoleChange(event.target.value as RolePresence)}
          aria-label={`Role for ${character.name}`}
        >
          {ROLE_OPTIONS.map((role) => (
            <option key={role} value={role}>
              {ROLE_LABEL[role]}
            </option>
          ))}
        </select>
        <div className={styles.name}>{character.name}</div>
        {character.traits && character.traits.length > 0 ? (
          <div className={styles.traits}>{character.traits.slice(0, 3).join(" · ")}</div>
        ) : null}
      </div>

      {isEditingActor ? (
        <input
          className={styles.actorInput}
          type="text"
          value={draftActor}
          disabled={disabled}
          autoFocus
          placeholder="Cast a specific actor for this role…"
          aria-label={`Preferred actor for ${character.name}`}
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
            <span className={styles.actorChosen}>&rarr; {character.preferred_actor}</span>
          ) : (
            <span className={styles.actorPlaceholder}>+ cast a specific actor</span>
          )}
        </button>
      )}
    </div>
  )
}
