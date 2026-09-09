import { NavLink } from "react-router-dom"
import { useAppState } from "../../state/AppStateContext"
import { useAuth } from "../../state/AuthContext"
import styles from "./NavBar.module.css"

const NAV_ITEMS = [{ to: "/about", label: "About" }]

export function NavBar() {
  const { screenplay, reset } = useAppState()
  const { user, signOut } = useAuth()

  // Clear the screenplay and report on the way out so the next account to sign
  // in on this browser does not land on the previous one's roster.
  async function handleSignOut() {
    await signOut()
    reset()
  }

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
            className={({ isActive }) => (isActive ? styles.linkActive : styles.link)}
          >
            {item.label}
          </NavLink>
        ))}
        {user ? (
          <div className={styles.account}>
            {user.photoURL ? (
              <img className={styles.avatar} src={user.photoURL} alt="" width={24} height={24} referrerPolicy="no-referrer" />
            ) : null}
            <span className={styles.accountName}>{user.displayName ?? user.email}</span>
            <button type="button" className={styles.signOut} onClick={() => void handleSignOut()}>
              Sign out
            </button>
          </div>
        ) : null}
      </nav>
    </header>
  )
}
