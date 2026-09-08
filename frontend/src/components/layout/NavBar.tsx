import { NavLink } from "react-router-dom"
import { useAppState } from "../../state/AppStateContext"
import styles from "./NavBar.module.css"

const NAV_ITEMS = [
  { to: "/", label: "Ingest", end: true },
  { to: "/roster", label: "Roster" },
  { to: "/casting-sheet", label: "Casting sheet" },
  { to: "/about", label: "About" },
]

export function NavBar() {
  const { screenplay } = useAppState()

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <span className={styles.logo} aria-hidden="true">
          🎬
        </span>
        <span className={styles.name}>Raphael</span>
        {screenplay ? <span className={styles.title}>/ {screenplay.title}</span> : null}
      </div>
      <nav className={styles.nav}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => (isActive ? styles.linkActive : styles.link)}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}
