import { Shimmer } from "../common/Shimmer"
import styles from "./BreakdownSkeleton.module.css"

/** Stand-in for the character list while POST /analyze is in flight. */
export function BreakdownSkeleton() {
  return (
    <div className={styles.wrapper}>
      <div className={styles.headline}>
        <Shimmer height={12} width="56%" />
        <div className={styles.headlineTags}>
          <Shimmer height={20} width="64px" />
          <Shimmer height={20} width="78px" delay={0.15} />
          <Shimmer height={20} width="92px" delay={0.3} />
        </div>
      </div>
      {[0, 1, 2, 3, 4].map((row) => (
        <div key={row} className={styles.row}>
          <Shimmer height={16} width="44px" delay={row * 0.1} />
          <Shimmer height={12} width="100%" delay={row * 0.1 + 0.05} />
          <Shimmer height={8} width="90px" delay={row * 0.1 + 0.1} />
        </div>
      ))}
    </div>
  )
}
