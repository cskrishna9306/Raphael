import { Navigate, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "../state/AuthContext"
import { Button } from "../components/common/Button"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { GoogleMark } from "../components/auth/GoogleMark"
import styles from "./LoginPage.module.css"

export function LoginPage() {
  const { user, initializing, error, signIn, skipSignIn } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const from = (location.state as { from?: string } | null)?.from

  if (initializing) return <div className={styles.page} aria-busy="true" />

  // Send an already-signed-in user back to whichever page brought them here.
  if (user) {
    return <Navigate to={from ?? "/"} replace />
  }

  function handleSkip() {
    skipSignIn()
    navigate(from ?? "/", { replace: true })
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
        <div className={styles.subhead}>Signing in is optional -- Raphael works the same either way, this just attaches your name to the session.</div>

        {error ? <ErrorBanner message={error} /> : null}

        <Button variant="primary" className={styles.action} onClick={() => void signIn()}>
          <GoogleMark />
          Continue with Google
        </Button>

        <button type="button" className={styles.skip} onClick={handleSkip}>
          Continue without signing in →
        </button>

        <div className={styles.footnote}>
          Raphael only reads your name, email and profile photo. Recommendations are decision support, not a shortlist
          to sign.
        </div>
      </div>
    </div>
  )
}
