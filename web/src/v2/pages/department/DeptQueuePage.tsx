import { OfficerPage as V1OfficerPage } from '@/pages/officer/OfficerPage'
import { useAuth } from '@/v2/auth'

/** Review queue: reuses the existing Officer page/drawer. The signed-in role seeds the role selector by
 * writing to the same localStorage key the v1 page reads, so a Tahsildar signing in lands acting as Tahsildar. */
export function DeptQueuePage() {
  const { profile } = useAuth()
  if (profile?.kind === 'department') {
    try {
      localStorage.setItem('sevaicheck.officerRole', profile.role)
    } catch {
      // storage unavailable: the officer page falls back to "all stages"
    }
  }
  return <V1OfficerPage />
}
