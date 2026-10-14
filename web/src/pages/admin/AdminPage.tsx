// Admin dashboard (P2-3): KPI strip → district map beside the alerts panel → charts → office table → reports.
import { FlaskConical } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'

import { getOffices, getOperationsMetrics, listAlerts, listIssueReports } from '@/api/client'
import type { Alert, IssueReport, Office, OperationsMetrics } from '@/api/types'
import { useLang } from '@/i18n'
import { AlertsPanel } from '@/pages/admin/AlertsPanel'
import { BacklogChart, DailyFlowChart, IssuesChart } from '@/pages/admin/Charts'
import { KpiStrip } from '@/pages/admin/KpiStrip'
import { OfficeMap } from '@/pages/admin/OfficeMap'
import { OfficeTable } from '@/pages/admin/OfficeTable'
import { RecentReports } from '@/pages/admin/RecentReports'

const LIVE_POLL_MS = 15_000 // alerts and reports (a new issue report shows up within seconds)
const METRICS_POLL_MS = 60_000

export function AdminPage() {
  const { t } = useLang()
  const [month, setMonth] = useState<OperationsMetrics | null>(null)
  const [week, setWeek] = useState<OperationsMetrics | null>(null)
  const [alerts, setAlerts] = useState<Alert[] | null>(null)
  const [reports, setReports] = useState<IssueReport[] | null>(null)
  const [offices, setOffices] = useState<Office[]>([])

  const loadMetrics = useCallback(async () => {
    try {
      const [m, w] = await Promise.all([getOperationsMetrics(30), getOperationsMetrics(7)])
      setMonth(m)
      setWeek(w)
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    }
  }, [t])

  const loadLive = useCallback(async () => {
    try {
      const [a, r] = await Promise.all([listAlerts(), listIssueReports()])
      setAlerts(a)
      setReports(r.slice(0, 15))
    } catch {
      // keep the last good data; the next poll retries
    }
  }, [])

  useEffect(() => {
    getOffices().then(setOffices).catch(() => {})
    loadMetrics()
    loadLive()
    const live = setInterval(loadLive, LIVE_POLL_MS)
    const metrics = setInterval(loadMetrics, METRICS_POLL_MS)
    return () => {
      clearInterval(live)
      clearInterval(metrics)
    }
  }, [loadLive, loadMetrics])

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('admin.title')}</h1>
        <p className="text-muted-foreground">{t('admin.subtitle')}</p>
      </div>
      {(month?.source ?? 'seed') !== 'live' && (
        <p className="flex items-center gap-2 rounded-lg border border-warning/30 bg-warning-soft/60 px-3 py-2 text-sm text-warning">
          <FlaskConical className="size-4 shrink-0" aria-hidden />
          {t('admin.banner')}
          {month?.source === 'FIXTURE' && <b className="ml-1">FIXTURE</b>}
        </p>
      )}

      <KpiStrip metrics={month} />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <section aria-label={t('admin.map')} className="space-y-2">
          <h2 className="text-sm font-semibold">{t('admin.map')}</h2>
          <OfficeMap week={week} />
        </section>
        <div className="lg:pt-7">
          <AlertsPanel alerts={alerts} onChanged={loadLive} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <DailyFlowChart daily={month?.daily ?? null} />
        <BacklogChart daily={month?.daily ?? null} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <OfficeTable rows={month?.by_office ?? null} />
        <div className="space-y-4">
          <IssuesChart byIssue={month?.by_issue ?? null} />
          <RecentReports reports={reports} offices={offices} />
        </div>
      </div>
    </div>
  )
}
