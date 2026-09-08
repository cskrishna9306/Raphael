import styles from "./Shimmer.module.css"

interface ShimmerProps {
  width?: string
  height?: number
  delay?: number
}

/** Placeholder bar standing in for content that's still streaming in. */
export function Shimmer({ width = "100%", height = 12, delay = 0 }: ShimmerProps) {
  return <div className={styles.shimmer} style={{ width, height, animationDelay: `${delay}s` }} />
}
