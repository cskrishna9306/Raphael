import styles from "./AvatarPlaceholder.module.css"

/**
 * Raphael's API doesn't return headshots, so every candidate gets this
 * cross-hatched placeholder instead of a broken/missing image.
 */
export function AvatarPlaceholder({ width, height }: { width: number; height: number }) {
  return <div className={styles.placeholder} style={{ width, height }} />
}
