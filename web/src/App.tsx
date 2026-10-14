import { Navigate, Route, Routes } from 'react-router-dom'

import { ApplyPage } from '@/v2/pages/citizen/ApplyPage'
import { CentresPage } from '@/v2/pages/citizen/CentresPage'
import { CitizenLayout } from '@/v2/pages/citizen/CitizenLayout'
import { HomePage } from '@/v2/pages/citizen/HomePage'
import { NewsPage } from '@/v2/pages/citizen/NewsPage'
import { ReportPage } from '@/v2/pages/citizen/ReportPage'
import { ServicesPage } from '@/v2/pages/citizen/ServicesPage'
import { TrackDetailPage } from '@/v2/pages/citizen/TrackDetailPage'
import { TrackPage } from '@/v2/pages/citizen/TrackPage'
import { CitizenLoginPage } from '@/v2/pages/CitizenLoginPage'
import { DeptMetricsPage } from '@/v2/pages/department/DeptMetricsPage'
import { DepartmentLayout } from '@/v2/pages/department/DepartmentLayout'
import { DeptQueuePage } from '@/v2/pages/department/DeptQueuePage'
import { DistrictPage } from '@/v2/pages/department/DistrictPage'
import { DepartmentLoginPage } from '@/v2/pages/DepartmentLoginPage'
import { LandingPage } from '@/v2/pages/LandingPage'
import { AuthProvider } from '@/v2/auth'
import { RequireAuth } from '@/v2/components/RequireAuth'
import { ScrollToTop } from '@/v2/scroll'

export default function App() {
  return (
    <AuthProvider>
      <ScrollToTop />
      <Routes>
        <Route index element={<LandingPage />} />
        <Route path="login" element={<CitizenLoginPage />} />
        <Route path="department-login" element={<DepartmentLoginPage />} />

        <Route element={<RequireAuth kind="citizen" loginPath="/login" />}>
          <Route path="portal" element={<CitizenLayout />}>
            <Route index element={<HomePage />} />
            <Route path="services" element={<ServicesPage />} />
            <Route path="apply/:service" element={<ApplyPage />} />
            <Route path="track" element={<TrackPage />} />
            <Route path="track/:id" element={<TrackDetailPage />} />
            <Route path="centres" element={<CentresPage />} />
            <Route path="news" element={<NewsPage />} />
            <Route path="report" element={<ReportPage />} />
          </Route>
        </Route>

        <Route element={<RequireAuth kind="department" loginPath="/department-login" />}>
          <Route path="department" element={<DepartmentLayout />}>
            <Route index element={<DeptQueuePage />} />
            <Route path="district" element={<DistrictPage />} />
            <Route path="metrics" element={<DeptMetricsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
