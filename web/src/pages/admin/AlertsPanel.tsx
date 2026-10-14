import { BellRing, Check, Lightbulb, MapPin } from 'lucide-react'
import { toast } from 'sonner'

import { ackAlert } from '@/api/client'
import type { Alert, AlertRule, AlertSeverity } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useLang } from '@/i18n'
import { dateTime } from '@/lib/format'
import { cn } from '@/lib/utils'

const SEVERITY: Record<AlertSeverity, string> = {
  high: 'bg-danger-soft text-danger',
  medium: 'bg-warning-soft text-warning',
  low: 'bg-secondary text-muted-foreground',
}

const RULE_LABEL: Record<AlertRule, string> = {
  REJECT_SPIKE: 'Rejection spike',
  SLA_BREACH: 'SLA breach',
  BACKLOG_GROWTH: 'Backlog growth',
  DUPLICATE_CLUSTER: 'Duplicate Aadhaar',
  USER_REPORTED: 'User reports',
}

function AlertCard({ alert, onAcked }: { alert: Alert; onAcked: () => void }) {
  const { t } = useLang()
  const acked = alert.status === 'acknowledged'

  async function ack() {
    try {
      await ackAlert(alert.id)
      onAcked()
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    }
  }

  return (
    <li className={cn('space-y-2 rounded-lg border bg-card p-3 transition-opacity', acked && 'opacity-60')}>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className={cn('rounded px-1.5 py-0.5 font-semibold uppercase', SEVERITY[alert.severity])}>{alert.severity}</span>
        <span className="font-medium text-muted-foreground">{RULE_LABEL[alert.rule]}</span>
        <span className="ml-auto text-muted-foreground">{dateTime(alert.created_at)}</span>
      </div>
      <p className="font-semibold leading-snug">{alert.title_en}</p>
      {alert.office_name && (
        <p className="flex items-center gap-1 text-xs text-muted-foreground">
          <MapPin className="size-3.5" aria-hidden />
          {alert.office_name}
        </p>
      )}
      <p className="text-sm text-muted-foreground">{alert.detail_en}</p>
      <div className="flex gap-2 rounded-md bg-accent/60 px-2.5 py-2 text-sm">
        <Lightbulb className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden />
        <p>
          <span className="sr-only">{t('admin.action')}: </span>
          {alert.suggested_action_en}
        </p>
      </div>
      {acked ? (
        <p className="flex items-center gap-1 text-xs text-muted-foreground">
          <Check className="size-3.5" aria-hidden />
          {t('admin.acked')}
        </p>
      ) : (
        <Button size="sm" variant="outline" onClick={ack}>
          <Check aria-hidden />
          {t('admin.ack')}
        </Button>
      )}
    </li>
  )
}

// Tie-breakers for alerts raised in the same minute: severity, then cause before effect.
const SEVERITY_RANK: Record<AlertSeverity, number> = { high: 0, medium: 1, low: 2 }
const RULE_RANK: Record<AlertRule, number> = {
  REJECT_SPIKE: 0,
  USER_REPORTED: 1,
  SLA_BREACH: 2,
  DUPLICATE_CLUSTER: 3,
  BACKLOG_GROWTH: 4,
}

function compareAlerts(a: Alert, b: Alert): number {
  return (
    Number(a.status !== 'open') - Number(b.status !== 'open') ||
    b.created_at.slice(0, 16).localeCompare(a.created_at.slice(0, 16)) ||
    SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity] ||
    RULE_RANK[a.rule] - RULE_RANK[b.rule]
  )
}

/** Open alerts first (newest first), acknowledged ones after them, dimmed. */
export function AlertsPanel({ alerts, onChanged }: { alerts: Alert[] | null; onChanged: () => void }) {
  const { t } = useLang()
  const ordered = alerts ? [...alerts].sort(compareAlerts) : []
  const open = alerts?.filter((a) => a.status === 'open').length ?? 0

  return (
    <section className="flex h-[440px] flex-col rounded-lg border bg-background">
      <h2 className="flex items-center gap-2 border-b px-3 py-2.5 text-sm font-semibold">
        <BellRing className="size-4 text-primary" aria-hidden />
        {t('admin.alerts')}
        {open > 0 && <span className="rounded-full bg-danger px-2 text-xs text-white tabular-nums">{open}</span>}
      </h2>
      <ul className="flex-1 space-y-2.5 overflow-y-auto p-3" aria-live="polite">
        {alerts === null && Array.from({ length: 3 }, (_, i) => <Skeleton key={i} className="h-32 w-full" />)}
        {alerts?.length === 0 && <p className="py-8 text-center text-sm text-muted-foreground">{t('admin.noAlerts')}</p>}
        {ordered.map((a) => (
          <AlertCard key={a.id} alert={a} onAcked={onChanged} />
        ))}
      </ul>
    </section>
  )
}
