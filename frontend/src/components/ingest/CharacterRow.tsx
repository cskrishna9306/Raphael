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
  disabled?: boolean
}

export function CharacterRow({ character, onRoleChange, disabled }: CharacterRowProps) {
  const isLead = character.role_presence === "lead"

  return (
    <div className={[styles.row, isLead ? styles.rowLead : ""].join(" ")}>
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
  )
}
