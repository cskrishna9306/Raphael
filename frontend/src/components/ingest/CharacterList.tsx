import type { CharacterProfile, RolePresence } from "../../api/types"
import { CharacterRow } from "./CharacterRow"
import styles from "./CharacterList.module.css"

interface CharacterListProps {
  characters: CharacterProfile[]
  onRoleChange: (characterName: string, role: RolePresence) => void
  onPreferredActorChange: (characterName: string, value: string | null) => void
  disabled?: boolean
}

export function CharacterList({ characters, onRoleChange, onPreferredActorChange, disabled }: CharacterListProps) {
  if (characters.length === 0) {
    return <div className={styles.empty}>No characters detected yet.</div>
  }

  return (
    <div className={styles.list}>
      {characters.map((character) => (
        <CharacterRow
          key={character.name}
          character={character}
          disabled={disabled}
          onRoleChange={(role) => onRoleChange(character.name, role)}
          onPreferredActorChange={(value) => onPreferredActorChange(character.name, value)}
        />
      ))}
    </div>
  )
}
