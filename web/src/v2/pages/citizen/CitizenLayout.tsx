import { Outlet } from 'react-router-dom'

import { useLang } from '@/i18n'
import { PortalFooter } from '@/v2/components/PortalFooter'
import { PortalHeader } from '@/v2/components/PortalHeader'

/** Shell for every citizen-portal page: header + nav, page content, footer. */
export function CitizenLayout() {
  const { t } = useLang()
  const nav = [
    { to: '/portal', label: t('v2.nav.home') },
    { to: '/portal/services', label: t('v2.services.title') },
    { to: '/portal/track', label: t('v2.home.track') },
    { to: '/portal/centres', label: t('v2.home.centres') },
    { to: '/portal/news', label: t('v2.news.title') },
    { to: '/portal/report', label: t('v2.home.report') },
  ]
  return (
    <div className="flex min-h-screen flex-col">
      <PortalHeader nav={nav} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <PortalFooter />
    </div>
  )
}
