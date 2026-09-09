import { initializeApp } from "firebase/app"
import { getAuth, GoogleAuthProvider } from "firebase/auth"

// These are public client identifiers, not secrets -- they ship inside the
// built bundle. They live in env vars only so the app can be pointed at a
// different Firebase project without a code change.
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

if (!firebaseConfig.apiKey) {
  throw new Error("Missing VITE_FIREBASE_* env vars -- copy frontend/.env.example to frontend/.env")
}

export const auth = getAuth(initializeApp(firebaseConfig))

export const googleProvider = new GoogleAuthProvider()
