import { Navigate, Outlet, useLocation } from "react-router-dom"
import { useAuth } from "../../state/AuthContext"
import styles from "./RequireAuth.module.css"

/**
 * Layout route that gates everything behind it on a signed-in Google account.
 * Renders nothing while Firebase restores a persisted session, so a returning
 * user is never bounced to the login page before that resolves.
 */
export function RequireAuth() {
  const { user, initializing } = useAuth()
  const location = useLocation()

  if (initializing) {
    return <div className={styles.pending} aria-busy="true" />
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
