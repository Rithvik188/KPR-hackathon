import { BellRing, Check, Lightbulb, RefreshCw } from 'lucide-react'

import type { Alert, AlertRule, AlertSeverity } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { type I18nKey, useLang } from '@/i18n'
import { dateTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import { SEVERITY } from '@/pages/admin/AlertsPanel'
import { useAuth } from '@/v2/auth'
import { Breadcrumbs } from '@/v2/components/Breadcrumbs'
import { useNotices } from '@/v2/pages/operator/useNotices'

const RULE_KEY: Record<AlertRule, I18nKey> = {
  REJECT_SPIKE: 'v2.notices.rule.REJECT_SPIKE',
  SLA_BREACH: 'v2.notices.rule.SLA_BREACH',
  BACKLOG_GROWTH: 'v2.notices.rule.BACKLOG_GROWTH',
  DUPLICATE_CLUSTER: 'v2.notices.rule.DUPLICATE_CLUSTER',
  USER_REPORTED: 'v2.notices.rule.USER_REPORTED',
}

const SEVERITY_KEY: Record<AlertSeverity, I18nKey> = {
  high: 'v2.notices.severity.high',
  medium: 'v2.notices.severity.medium',
  low: 'v2.notices.severity.low',
}

/** Read-only version of the admin alert card: operators see what the district office sees about their centre,
 * but acknowledging stays an admin action. Alert text comes from the rules engine (English only). */
function NoticeCard({ alert }: { alert: Alert }) {
  const { t } = useLang()
  const acked = alert.status === 'acknowledged'
  return (
    <li className={cn('space-y-2 rounded-lg border bg-card p-4', acked && 'opacity-60')}>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className={cn('rounded px-1.5 py-0.5 font-semibold uppercase', SEVERITY[alert.severity])}>{t(SEVERITY_KEY[alert.severity])}</span>
        <span className="font-medium text-muted-foreground">{t(RULE_KEY[alert.rule])}</span>
        <span className="ml-auto text-muted-foreground">{dateTime(alert.created_at)}</span>
      </div>
      <p className="font-semibold leading-snug">{alert.title_en}</p>
      <p className="text-sm text-muted-foreground">{alert.detail_en}</p>
      <div className="flex gap-2 rounded-md bg-accent/60 px-2.5 py-2 text-sm">
        <Lightbulb className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden />
        <p>
          <span className="font-medium">{t('v2.notices.whatToDo')}: </span>
          {alert.suggested_action_en}
        </p>
      </div>
      {acked && (
        <p className="flex items-center gap-1 text-xs text-muted-foreground">
          <Check className="size-3.5" aria-hidden />
          {t('v2.notices.acknowledged')}
        </p>
      )}
    </li>
  )
}

/** Notices: alerts the rules engine raised for the operator's own centre only. */
export function NoticesPage() {
  const { t } = useLang()
  const { profile } = useAuth()
  const operator = profile?.kind === 'operator' ? profile : null
  const { alerts, failed, reload } = useNotices(operator?.officeId)
  const open = alerts?.filter((a) => a.status === 'open').length ?? 0

  return (
    <div className="space-y-5">
      <Breadcrumbs items={[{ label: t('v2.notices.title') }]} />
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
            <BellRing className="size-6 text-primary" aria-hidden />
            {t('v2.notices.title')}
            {open > 0 && <span className="rounded-full bg-danger px-2 text-sm text-white tabular-nums">{open}</span>}
          </h1>
          <p className="text-muted-foreground">{t('v2.notices.subtitle', { office: operator?.officeName ?? '' })}</p>
        </div>
        <Button variant="outline" size="sm" onClick={reload}>
          <RefreshCw aria-hidden />
          {t('v2.notices.refresh')}
        </Button>
      </div>

      {operator && (
        <Badge className={operator.centreType === 'govt' ? 'bg-accent text-primary' : 'bg-secondary text-foreground'}>
          {t(operator.centreType === 'govt' ? 'v2.operator.centreGovt' : 'v2.operator.centrePrivate')}
        </Badge>
      )}

      {failed && <p className="text-sm text-danger">{t('common.error')}</p>}

      <ul className="space-y-3" aria-live="polite">
        {alerts === null && Array.from({ length: 2 }, (_, i) => <Skeleton key={i} className="h-36 w-full" />)}
        {alerts?.map((a) => (
          <NoticeCard key={a.id} alert={a} />
        ))}
      </ul>
      {alerts?.length === 0 && !failed && (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">{t('v2.notices.empty')}</CardContent>
        </Card>
      )}
    </div>
  )
}
