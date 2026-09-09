import { Navigate, Outlet, useLocation } from "react-router-dom"
import { useAuth } from "../../state/AuthContext"
import styles from "./AuthGate.module.css"

/**
 * Layout route that shows the sign-in page first for a fresh session, but
 * never hard-requires it -- signing in is optional (see src/raphael/auth.py's
 * optional_claims), so once the user signs in *or* explicitly skips (see
 * LoginPage), this lets them straight through from then on. Renders nothing
 * while Firebase restores a persisted session, so a returning signed-in user
 * is never bounced to the login page before that resolves.
 */
export function AuthGate() {
  const { user, initializing, skipped } = useAuth()
  const location = useLocation()

  if (initializing) {
    return <div className={styles.pending} aria-busy="true" />
  }

  if (!user && !skipped) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
