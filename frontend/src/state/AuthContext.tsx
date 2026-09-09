import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { onAuthStateChanged, signInWithPopup, signOut as firebaseSignOut, type User } from "firebase/auth"
import { auth, googleProvider } from "../firebase"

interface AuthState {
  user: User | null
  /** True until Firebase has restored (or ruled out) a persisted session. */
  initializing: boolean
  error: string | null
  signIn: () => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

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
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [initializing, setInitializing] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
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
      signIn: async () => {
        setError(null)
        try {
          await signInWithPopup(auth, googleProvider)
        } catch (caught) {
          setError(describeAuthError(caught))
        }
      },
      signOut: async () => {
        setError(null)
        await firebaseSignOut(auth)
      },
    }),
    [user, initializing, error],
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
