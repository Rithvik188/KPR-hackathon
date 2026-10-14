import { OfficerPage as V1OfficerPage } from '@/pages/officer/OfficerPage'
import { useAuth } from '@/v2/auth'

/** Review queue: reuses the existing Officer page/drawer, locked to the signed-in role. A VAO can never act
 * as RI or Tahsildar — there is no in-page way to switch, unlike the old (removed) role selector. */
export function DeptQueuePage() {
  const { profile } = useAuth()
  const role = profile?.kind === 'department' ? profile.role : undefined
  return <V1OfficerPage lockedRole={role} />
}
