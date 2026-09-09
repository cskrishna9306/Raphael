import styles from "./AvatarPlaceholder.module.css"

/**
 * Fallback for a candidate with no headshot URL (or whose image failed to
 * load) -- see Avatar, which is what picks between this and a real image.
 */
export function AvatarPlaceholder({ width, height }: { width: number; height: number }) {
  return <div className={styles.placeholder} style={{ width, height }} />
}
