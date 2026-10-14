import { Outlet } from 'react-router-dom'

import { useLang } from '@/i18n'
import { PortalFooter } from '@/v2/components/PortalFooter'
import { PortalHeader } from '@/v2/components/PortalHeader'

/** Shell for the department workspace: officer queue, district overview and accuracy metrics. */
export function DepartmentLayout() {
  const { t } = useLang()
  const nav = [
    { to: '/department', label: t('v2.dept.queue') },
    { to: '/department/district', label: t('v2.dept.district') },
    { to: '/department/metrics', label: t('v2.dept.metrics') },
  ]
  return (
    <div className="flex min-h-screen flex-col">
      <PortalHeader homeHref="/department" nav={nav} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <PortalFooter />
    </div>
  )
}
