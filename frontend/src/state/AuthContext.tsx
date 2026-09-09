import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { onAuthStateChanged, signInWithPopup, signOut as firebaseSignOut, type User } from "firebase/auth"
import { auth, googleProvider } from "../firebase"

interface AuthState {
  user: User | null
  /** True until Firebase has restored (or ruled out) a persisted session. */
  initializing: boolean
  error: string | null
  /** True once the user has explicitly chosen to continue without signing in, for this browser session. */
  skipped: boolean
  signIn: () => Promise<void>
  signOut: () => Promise<void>
  skipSignIn: () => void
}

const AuthContext = createContext<AuthState | null>(null)

// sessionStorage (not localStorage) on purpose: the sign-in page should greet
// every fresh session, but shouldn't nag again once someone's already chosen
// to skip it within the current tab/browser session.
const SKIP_KEY = "raphael:skippedSignIn"

// Closing the Google popup, or opening a second one, is a normal user action
// rather than a failure -- neither should surface an error in the UI.
const SILENT_AUTH_ERRORS = new Set(["auth/popup-closed-by-user", "auth/cancelled-popup-request"])

function describeAuthError(error: unknown): string | null {
  const code = (error as { code?: string })?.code
  if (code && SILENT_AUTH_ERRORS.has(code)) return null
  if (code === "auth/popup-blocked") return "Your browser blocked the sign-in popup. Allow popups for this site and try again."
  if (code === "auth/unauthorized-domain") return "This domain is not authorised for sign-in in the Firebase console."
  return "Sign-in failed. Try again."
}

/**
 * Tracks the signed-in Google account for the whole app. Firebase persists the
 * session in browser storage and refreshes ID tokens on its own, so this only
 * has to mirror `onAuthStateChanged` into React state.
 *
 * `auth` (from ../firebase) is null when Firebase isn't configured for this
 * deployment -- signing in is optional, so that must degrade to "sign-in
 * unavailable" here, not crash the app that imports this provider.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [initializing, setInitializing] = useState(auth !== null)
  const [error, setError] = useState<string | null>(null)
  const [skipped, setSkipped] = useState(() => sessionStorage.getItem(SKIP_KEY) === "1")

  useEffect(() => {
    if (!auth) return
    return onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser)
      setInitializing(false)
    })
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      user,
      initializing,
      error,
      skipped,
      signIn: async () => {
        setError(null)
        if (!auth) {
          setError("Sign-in isn't configured for this deployment. You can still use Raphael without an account.")
          return
        }
        try {
          await signInWithPopup(auth, googleProvider)
        } catch (caught) {
          setError(describeAuthError(caught))
        }
      },
      signOut: async () => {
        setError(null)
        // A signed-out user should see the sign-in-or-skip choice again, same as a fresh session.
        sessionStorage.removeItem(SKIP_KEY)
        setSkipped(false)
        if (!auth) return
        await firebaseSignOut(auth)
      },
      skipSignIn: () => {
        sessionStorage.setItem(SKIP_KEY, "1")
        setSkipped(true)
      },
    }),
    [user, initializing, error, skipped],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
