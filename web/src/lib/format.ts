// Display helpers. All API timestamps are UTC ISO strings; the UI shows Indian Standard Time.

const IST = 'Asia/Kolkata'

export function seconds(ms: number): string {
  return (ms / 1000).toFixed(ms < 10_000 ? 1 : 0)
}

/** "1998-04-12" -> "12/04/1998" (dates of birth are calendar dates, no timezone shift). */
export function isoDateToDisplay(value: string | null | undefined): string {
  if (!value) return '—'
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  return m ? `${m[3]}/${m[2]}/${m[1]}` : value
}

export function dateTime(iso: string): string {
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: IST,
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export function timeOnly(iso: string): string {
  return new Intl.DateTimeFormat('en-IN', { timeZone: IST, hour: '2-digit', minute: '2-digit' }).format(new Date(iso))
}

export function percent(rate: number, digits = 0): string {
  return `${(rate * 100).toFixed(digits)}%`
}
