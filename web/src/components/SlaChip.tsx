import { Clock } from 'lucide-react'

import type { AppStatus } from '@/api/types'
import { useLang } from '@/i18n'
import { cn } from '@/lib/utils'

const DECIDED: AppStatus[] = ['approved', 'rejected']

/** SLA countdown: red once breached, amber under 12 h, muted otherwise. Decided applications show a dash. */
export function SlaChip({ hoursLeft, status }: { hoursLeft: number; status: AppStatus }) {
  const { t } = useLang()
  if (DECIDED.includes(status)) return <span className="text-muted-foreground">—</span>
  const overdue = hoursLeft < 0
  const h = Math.abs(hoursLeft) >= 10 ? Math.round(Math.abs(hoursLeft)) : Math.abs(hoursLeft).toFixed(1)
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap tabular-nums',
        overdue ? 'bg-danger-soft text-danger' : hoursLeft < 12 ? 'bg-warning-soft text-warning' : 'text-muted-foreground',
      )}
    >
      <Clock className="size-3.5" aria-hidden />
      {t(overdue ? 'officer.slaOverdue' : 'officer.slaLeft', { h })}
    </span>
  )
}

/** Per-stage SLA (contract v1.4): how long the current officer has left, red once overdue. */
export function StageSlaChip({ hoursLeft }: { hoursLeft: number | null | undefined }) {
  const { t } = useLang()
  if (hoursLeft === null || hoursLeft === undefined) return null
  const overdue = hoursLeft < 0
  const h = Math.abs(hoursLeft) >= 10 ? Math.round(Math.abs(hoursLeft)) : Math.abs(hoursLeft).toFixed(1)
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap tabular-nums',
        overdue ? 'bg-danger-soft text-danger' : hoursLeft < 6 ? 'bg-warning-soft text-warning' : 'bg-muted text-muted-foreground',
      )}
    >
      <Clock className="size-3.5" aria-hidden />
      {t(overdue ? 'stage.overdue' : 'stage.dueIn', { h })}
    </span>
  )
}
