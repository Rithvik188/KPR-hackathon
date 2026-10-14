import { Navigate, Outlet, Route, Routes } from 'react-router-dom'

import { TopBar } from '@/components/TopBar'
import { useLang } from '@/i18n'
import { ComingSoon } from '@/pages/ComingSoon'
import { CounterPage } from '@/pages/CounterPage'

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
        <Route path="officer" element={<ComingSoon title={t('nav.officer')} />} />
        <Route path="admin" element={<ComingSoon title={t('nav.admin')} />} />
        <Route path="metrics" element={<ComingSoon title={t('nav.metrics')} />} />
        <Route path="report" element={<ComingSoon title={t('nav.report')} />} />
        <Route path="*" element={<Navigate to="/counter" replace />} />
      </Route>
    </Routes>
  )
}
