# Raphael Frontend

React + TypeScript + Vite UI for Raphael. Talks to exactly two endpoints on
the FastAPI backend in `../src/raphael`: `POST /analyze` (screenplay
breakdown) and `POST /recommend` (casting, chemistry and risk pipeline).

## Screens

- **Ingest** (`/`): drop a `.txt`/`.pdf` screenplay, run the breakdown, review/edit detected characters, then run casting analysis
- **Roster** (`/roster`): ranked cast clusters as a lead/supporting/ensemble formation tree, with chemistry score and risk register per cluster
- **About** (`/about`): static explainer of how Raphael reasons and its contributors

## Setup

Requires Node.js >= 20 and npm.

```bash
cd frontend
npm install
cp .env.example .env   # only needed if the backend isn't on the default URL
```

## Running it

1. Start the backend first, from the repo root (see the top-level
   `README.md` for its own setup):

   ```bash
   uv run python -m src.raphael.main
   ```

   By default it listens on `http://localhost:8000`. The backend must allow
   CORS from this app's dev origin -- set `ALLOWED_ORIGINS` in the backend's
   `.env` if you're not using the default `http://localhost:5173`
   (`src/raphael/config.py`).

2. In a second terminal, start the frontend dev server:

   ```bash
   cd frontend
   npm run dev
   ```

   Open the printed URL (`http://localhost:5173` by default).

## Configuration

`VITE_API_BASE_URL` (see `.env.example`) points the app at the backend.
Defaults to `http://localhost:8000` if unset.

## Other scripts

```bash
npm run build     # type-check + production build to dist/
npm run preview   # serve the production build locally
npm run lint      # oxlint
```

## Deployment

Hosted on Firebase Hosting (project `cedar-calling-505608-s1`), config at the
repo root (`../firebase.json`, `../.firebaserc`) since it deploys the built
`frontend/dist` output, not the source tree.

**CI/CD**: `.github/workflows/deploy-frontend.yml` builds and deploys to
production automatically on every push to `main` that touches `frontend/**`
(or the Firebase config itself). Backend changes alone don't trigger it.

The production build needs the deployed backend's URL. Until the backend is
deployed, set it in the repo's GitHub Actions variables (Settings -> Secrets
and variables -> Actions -> Variables) as `VITE_API_BASE_URL` -- the workflow
reads it at build time. Unset, it falls back to `http://localhost:8000`,
which won't reach anything in production.

**Manual deploy** (e.g. to test before pushing):

```bash
npm run build
npx firebase-tools deploy --only hosting
```
