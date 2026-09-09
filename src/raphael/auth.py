# Import third-party packages
import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

# Import custom modules
from src.raphael.config import config

_bearer_scheme = HTTPBearer(auto_error=False)

def firebase_app() -> firebase_admin.App:
    """
    Returns the process-wide firebase_admin app, initializing it on first use.
    Shared by token verification and the Firestore client behind /projects.
    """

    # Initialized lazily rather than at import time so that importing this
    # module never requires credentials -- only verifying a token does. The
    # credentials come from ADC: the raphael@ service account on Cloud Run,
    # `gcloud auth application-default login` locally.
    try:
        return firebase_admin.get_app()
    except ValueError:
        return firebase_admin.initialize_app(options={"projectId": config.GOOGLE_CLOUD_PROJECT})

def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """
    Authenticates a request from the Firebase ID token in its Authorization
    header, returning the decoded claims (uid, email, name) for the signed-in
    Google account. Raises 401 if the token is missing, malformed or expired.
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Declared sync so FastAPI runs it in a threadpool -- verify_id_token
    # blocks on a (cached) fetch of Google's public signing keys.
    try:
        return firebase_auth.verify_id_token(credentials.credentials, app=firebase_app())
    except (ValueError, firebase_auth.InvalidIdTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired sign-in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
