import type { ReactNode } from "react"
import styles from "./Panel.module.css"

export function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={[styles.panel, className].filter(Boolean).join(" ")}>{children}</div>
}
