import { useState } from "react"
import { AvatarPlaceholder } from "./AvatarPlaceholder"
import styles from "./Avatar.module.css"

interface AvatarProps {
  src?: string | null
  alt: string
  width: number
  height: number
}

/**
 * Renders a candidate's headshot when one is available, falling back to
 * AvatarPlaceholder both when the API has no URL and when the URL 404s.
 */
export function Avatar({ src, alt, width, height }: AvatarProps) {
  const [failed, setFailed] = useState(false)

  if (!src || failed) {
    return <AvatarPlaceholder width={width} height={height} />
  }

  return (
    <img
      className={styles.image}
      src={src}
      alt={alt}
      width={width}
      height={height}
      onError={() => setFailed(true)}
    />
  )
}
