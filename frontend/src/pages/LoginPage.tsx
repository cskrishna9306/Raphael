import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../state/AuthContext"
import { Button } from "../components/common/Button"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { GoogleMark } from "../components/auth/GoogleMark"
import styles from "./LoginPage.module.css"

export function LoginPage() {
  const { user, initializing, error, signIn } = useAuth()
  const location = useLocation()

  if (initializing) return <div className={styles.page} aria-busy="true" />

  // Send an already-signed-in user back to whichever page bounced them here,
  // defaulting to ingest rather than "/" -- someone who came via the sign-in
  // tab wants the app, not the About page they just left.
  if (user) {
    const from = (location.state as { from?: string } | null)?.from
    return <Navigate to={from ?? "/ingest"} replace />
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.brand}>
          <span className={styles.logo} aria-hidden="true">
            🎬
          </span>
          <span className={styles.name}>Raphael</span>
        </div>

        <div className={styles.headline}>An agentic casting director that reads the script before it names a name.</div>
        <div className={styles.subhead}>Sign in with Google to upload a screenplay and run a casting breakdown.</div>

        {error ? <ErrorBanner message={error} /> : null}

        <Button variant="primary" className={styles.action} onClick={() => void signIn()}>
          <GoogleMark />
          Continue with Google
        </Button>

        <div className={styles.footnote}>
          Raphael only reads your name, email and profile photo. Recommendations are decision support, not a shortlist
          to sign.
        </div>
      </div>
    </div>
  )
}
