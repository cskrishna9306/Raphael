import { initializeApp } from "firebase/app"
import { getAuth, GoogleAuthProvider, type Auth } from "firebase/auth"

// These are public client identifiers, not secrets -- they ship inside the
// built bundle. They live in env vars only so the app can be pointed at a
// different Firebase project without a code change.
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

// Signing in is optional (the backend accepts anonymous requests -- see
// optional_claims), so a missing/misconfigured Firebase project must not take
// the whole app down with it. `auth` is null in that case; AuthContext treats
// that as "sign-in unavailable" rather than crashing at import time.
export const auth: Auth | null = firebaseConfig.apiKey ? getAuth(initializeApp(firebaseConfig)) : null

if (!auth) {
  console.warn("Sign-in is unavailable: missing VITE_FIREBASE_* env vars (copy frontend/.env.example to frontend/.env). The app works fine signed out.")
}

export const googleProvider = new GoogleAuthProvider()
