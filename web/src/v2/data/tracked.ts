// Application ids this browser has submitted, so Track can list them without a citizen account on the backend.
const KEY = 'sevaicheck.v2.trackedApplications'

export function trackedApplicationIds(): string[] {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

export function rememberApplication(id: string): void {
  try {
    const ids = trackedApplicationIds()
    if (!ids.includes(id)) localStorage.setItem(KEY, JSON.stringify([id, ...ids]))
  } catch {
    // storage unavailable: tracking lasts for this session only
  }
}
