const STORAGE_KEY = "raphael:ingest-file"

interface CachedFile {
  name: string
  type: string
  data: string
}

/**
 * Caches the dropped screenplay in sessionStorage (base64-encoded, since
 * File objects aren't serializable) so a page refresh doesn't force a
 * re-drop. Best-effort: silently no-ops on quota/storage errors.
 */
export async function cacheIngestFile(file: File): Promise<void> {
  try {
    const bytes = new Uint8Array(await file.arrayBuffer())
    let binary = ""
    for (const byte of bytes) binary += String.fromCharCode(byte)
    const cached: CachedFile = { name: file.name, type: file.type, data: btoa(binary) }
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(cached))
  } catch {
    // Ignore -- caching is a nice-to-have, not required for the upload flow.
  }
}

export function loadCachedIngestFile(): File | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const cached = JSON.parse(raw) as CachedFile
    const binary = atob(cached.data)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
    return new File([bytes], cached.name, { type: cached.type })
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export function clearCachedIngestFile(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // Ignore -- nothing to clean up if storage is unavailable.
  }
}
