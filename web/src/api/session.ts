// The signed-in session (contract v1.8): a server-issued, signed, expiring token. It lives in memory for the API
// client and in sessionStorage so it survives a reload but dies with the tab. It carries no personal data.
import type { Session } from './types'

const KEY = 'sevaicheck.v2.session'

function read(): Session | null {
  try {
    const raw = sessionStorage.getItem(KEY)
    const s = raw ? (JSON.parse(raw) as Session) : null
    return s?.token && s.expires_at * 1000 > Date.now() ? s : null
  } catch {
    return null
  }
}

let current: Session | null = read()
const expiredListeners = new Set<() => void>()

/** The current session, or null if there is none or it has run out. */
export function getSession(): Session | null {
  if (current && current.expires_at * 1000 <= Date.now()) clearSession()
  return current
}

export function setSession(session: Session) {
  current = session
  try {
    sessionStorage.setItem(KEY, JSON.stringify(session))
  } catch {
    // storage unavailable: the session lasts until this page is reloaded
  }
}

export function clearSession() {
  current = null
  try {
    sessionStorage.removeItem(KEY)
  } catch {
    // nothing stored
  }
}

/** Runs `fn` when the server rejects the session (401), so the app can send the user back to their login page. */
export function onSessionExpired(fn: () => void): () => void {
  expiredListeners.add(fn)
  return () => {
    expiredListeners.delete(fn)
  }
}

export function expireSession() {
  clearSession()
  expiredListeners.forEach((fn) => fn())
}
