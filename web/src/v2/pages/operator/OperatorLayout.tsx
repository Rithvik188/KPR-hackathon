import { Outlet } from 'react-router-dom'

import { useLang } from '@/i18n'
import { useAuth } from '@/v2/auth'
import { PortalFooter } from '@/v2/components/PortalFooter'
import { PortalHeader } from '@/v2/components/PortalHeader'

/** Shell for the e-Sevai operator portal: the citizen portal's pages minus Track application (operators don't
 * own applications), plus Notices for their own centre. */
export function OperatorLayout() {
  const { t } = useLang()
  const { profile } = useAuth()
  const officeId = profile?.kind === 'operator' ? profile.officeId : ''
  const nav = [
    { to: '/operator', label: t('v2.nav.home') },
    { to: '/operator/notices', label: t('v2.notices.title') },
    { to: '/operator/services', label: t('v2.services.title') },
    { to: '/operator/centres', label: t('v2.home.centres') },
    { to: '/operator/news', label: t('v2.news.title') },
    // The report form pre-selects ?office=, so an operator's reports are filed against their own centre.
    { to: `/operator/report?office=${encodeURIComponent(officeId)}`, label: t('v2.home.report') },
  ]
  return (
    <div className="flex min-h-screen flex-col">
      <PortalHeader homeHref="/operator" nav={nav} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <PortalFooter />
    </div>
  )
}
