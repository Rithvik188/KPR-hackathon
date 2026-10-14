import { MetricsPage as V1MetricsPage } from '@/pages/MetricsPage'

/** Accuracy metrics: reuses the existing Metrics page inside the v2 department shell. */
export function DeptMetricsPage() {
  return <V1MetricsPage />
}
