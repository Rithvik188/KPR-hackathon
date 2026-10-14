import { useCallback, useEffect, useState } from 'react'

import { listAlerts } from '@/api/client'
import type { Alert } from '@/api/types'
import { compareAlerts } from '@/pages/admin/AlertsPanel'

const POLL_MS = 30_000

/** Alerts for one office, sorted like the admin panel (open first, newest first). Filtered client-side as well
 * as by `?office_id=`, so an operator never sees another centre's notices whatever the server returns. */
export function useNotices(officeId: string | undefined) {
  const [alerts, setAlerts] = useState<Alert[] | null>(null)
  const [failed, setFailed] = useState(false)

  const load = useCallback(async () => {
    if (!officeId) return
    try {
      const all = await listAlerts(undefined, officeId)
      setAlerts(all.filter((a) => a.office_id === officeId).sort(compareAlerts))
      setFailed(false)
    } catch {
      setFailed(true)
      setAlerts((prev) => prev ?? [])
    }
  }, [officeId])

  useEffect(() => {
    load()
    const timer = setInterval(load, POLL_MS)
    return () => clearInterval(timer)
  }, [load])

  return { alerts, failed, reload: load }
}
