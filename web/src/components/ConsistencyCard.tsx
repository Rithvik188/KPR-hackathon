import { ArrowLeftRight, CalendarCheck, CalendarX } from 'lucide-react'

import type { ConsistencyResult, NameTier } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { useLang } from '@/i18n'
import { cn } from '@/lib/utils'

const TIER_STYLE: Record<NameTier, string> = {
  match: 'bg-success-soft text-success',
  likely_match: 'bg-warning-soft text-warning',
  mismatch: 'bg-danger-soft text-danger',
  not_enough_data: 'bg-secondary text-muted-foreground',
}

/** Names side by side with the tier badge and DOB result. Used on the counter and in the officer drawer. */
export function ConsistencyCard({ consistency, className }: { consistency: ConsistencyResult; className?: string }) {
  const { t } = useLang()
  const { name_tier, names_compared, dob_match, name_score } = consistency
  const expanded = consistency.issues.find((i) => i.evidence?.initial_expanded)?.evidence.initial_expanded as
    | string
    | undefined

  return (
    <div className={cn('space-y-3 rounded-lg border bg-background p-3', className)}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium">{t('consistency.title')}</p>
        <Badge className={cn('h-6 px-2.5 text-xs', TIER_STYLE[name_tier])}>{t(`tier.${name_tier}`)}</Badge>
      </div>
      {names_compared.length >= 2 && (
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 text-sm">
          <span className="truncate rounded-md bg-muted px-2 py-1.5 text-center font-medium">{names_compared[0]}</span>
          <ArrowLeftRight className="size-4 text-muted-foreground" aria-hidden />
          <span className="truncate rounded-md bg-muted px-2 py-1.5 text-center font-medium">{names_compared[1]}</span>
        </div>
      )}
      {(dob_match !== null || expanded || name_score !== null) && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
          {dob_match !== null && (
            <span className={cn('inline-flex items-center gap-1', dob_match ? 'text-success' : 'text-danger')}>
              {dob_match ? <CalendarCheck className="size-3.5" /> : <CalendarX className="size-3.5" />}
              {t(dob_match ? 'consistency.dobMatch' : 'consistency.dobMismatch')}
            </span>
          )}
          {expanded && <span className="font-mono">{expanded}</span>}
          {name_score !== null && <span>score {Math.round(name_score)}</span>}
        </div>
      )}
    </div>
  )
}
