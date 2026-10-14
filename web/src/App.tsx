import { Navigate, Outlet, Route, Routes } from 'react-router-dom'

import { TopBar } from '@/components/TopBar'
import { AdminPage } from '@/pages/admin/AdminPage'
import { CounterPage } from '@/pages/counter/CounterPage'
import { MetricsPage } from '@/pages/MetricsPage'
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
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/counter" replace />} />
        <Route path="counter" element={<CounterPage />} />
        <Route path="officer" element={<OfficerPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="metrics" element={<MetricsPage />} />
        <Route path="report" element={<ReportPage />} />
        <Route path="*" element={<Navigate to="/counter" replace />} />
      </Route>
    </Routes>
  )
}
