import { Navigate, Outlet, Route, Routes } from 'react-router-dom'

import { TopBar } from '@/components/TopBar'
import { useLang } from '@/i18n'
import { ComingSoon } from '@/pages/ComingSoon'
import { CounterPage } from '@/pages/counter/CounterPage'
import { AdminPage } from '@/pages/admin/AdminPage'
import { OfficerPage } from '@/pages/officer/OfficerPage'
import { ReportPage } from '@/pages/ReportPage'

function Layout() {
  return (
    <div className="min-h-screen">
      <TopBar />
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  const { t } = useLang()
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/counter" replace />} />
        <Route path="counter" element={<CounterPage />} />
        <Route path="officer" element={<OfficerPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="metrics" element={<ComingSoon title={t('nav.metrics')} />} />
        <Route path="report" element={<ReportPage />} />
        <Route path="*" element={<Navigate to="/counter" replace />} />
      </Route>
    </Routes>
  )
}
