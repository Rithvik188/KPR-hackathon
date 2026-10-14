import { useLang } from '@/i18n'
import { AdminPage as V1AdminPage } from '@/pages/admin/AdminPage'

/** District overview: reuses the existing Admin dashboard (map, alerts, charts) inside the v2 shell. */
export function DistrictPage() {
  useLang()
  return <V1AdminPage />
}
