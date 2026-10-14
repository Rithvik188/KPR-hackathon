import type { OperationsMetrics } from '@/api/types'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { type I18nKey, useLang } from '@/i18n'
import { percent } from '@/lib/format'
import { cn } from '@/lib/utils'

export function KpiStrip({ metrics }: { metrics: OperationsMetrics | null }) {
  const { t } = useLang()
  const tiles: { key: I18nKey; value: string; tone?: string }[] = metrics
    ? [
        { key: 'admin.kpi.applications', value: metrics.totals.applications.toLocaleString('en-IN') },
        { key: 'admin.kpi.ftr', value: percent(metrics.totals.first_time_right_rate) },
        { key: 'admin.kpi.resubmissions', value: metrics.totals.avg_resubmissions.toFixed(2) },
        { key: 'admin.kpi.backlog', value: metrics.totals.backlog_now.toLocaleString('en-IN') },
        {
          key: 'admin.kpi.sla',
          value: metrics.totals.sla_breaches_now.toLocaleString('en-IN'),
          tone: metrics.totals.sla_breaches_now > 0 ? 'text-danger' : undefined,
        },
      ]
    : []

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {metrics
        ? tiles.map((tile) => (
            <Card key={tile.key} className="gap-1 px-4 py-3">
              <p className="text-xs text-muted-foreground">{t(tile.key)}</p>
              <p className={cn('text-2xl font-semibold tabular-nums', tile.tone)}>{tile.value}</p>
            </Card>
          ))
        : Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-[74px] rounded-xl" />)}
    </div>
  )
}
