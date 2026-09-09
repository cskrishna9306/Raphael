import { NavLink, useNavigate } from "react-router-dom"
import { useAppState } from "../../state/AppStateContext"
import { useAuth } from "../../state/AuthContext"
import { toDisplayTitle } from "../../utils/format"
import styles from "./NavBar.module.css"

const NAV_ITEMS = [{ to: "/", label: "About" }]

export function NavBar() {
  const { screenplay, reset } = useAppState()
  const { user, initializing, signOut } = useAuth()
  const navigate = useNavigate()

  // Clear the screenplay and report on the way out so the next account to sign
  // in on this browser does not land on the previous one's roster.
  async function handleSignOut() {
    await signOut()
    reset()
    // Land on the public About page. Without this the protected page we were
    // on would bounce us to /login, which reads as an error rather than as
    // having signed out successfully.
    navigate("/")
  }

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <span className={styles.logo} aria-hidden="true">
          🎬
        </span>
        <span className={styles.name}>Raphael</span>
        {screenplay ? <span className={styles.title}>/ {toDisplayTitle(screenplay.title)}</span> : null}
      </div>
      <nav className={styles.nav}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            // `end` matters for "/": without it every route matches it as a
            // prefix and About would read as active everywhere.
            end
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
        ) : initializing ? null : (
          // Held back until Firebase has resolved the session, so a returning
          // user never sees "Sign in" flash before their account appears.
          <NavLink to="/login" className={styles.signIn}>
            Sign in
          </NavLink>
        )}
      </nav>
    </header>
  )
}
