import { Check } from 'lucide-react'

import type { AppStatus, Stage } from '@/api/types'
import { useLang } from '@/i18n'
import { STAGE_ORDER, stageName } from '@/lib/services'
import { cn } from '@/lib/utils'

/** The e-District approval chain: VAO → Revenue Inspector → Tahsildar. Done steps tick, the current one is filled. */
export function StageTrack({ stage, status }: { stage: Stage | null | undefined; status: AppStatus }) {
  const { lang, t } = useLang()
  const approved = status === 'approved'
  const current = stage ? STAGE_ORDER.indexOf(stage) : approved ? STAGE_ORDER.length : -1
  return (
    <ol className="flex items-start gap-1" aria-label={t('officer.chain')}>
      {STAGE_ORDER.map((s, i) => {
        const done = i < current
        const active = i === current
        return (
          <li key={s} className="flex flex-1 flex-col items-center gap-1 text-center">
            <span className="flex w-full items-center">
              <span className={cn('h-0.5 flex-1', i === 0 ? 'opacity-0' : done || active ? 'bg-primary' : 'bg-border')} />
              <span
                aria-current={active ? 'step' : undefined}
                className={cn(
                  'flex size-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold',
                  done && 'border-primary bg-primary text-primary-foreground',
                  active && 'border-primary bg-card text-primary ring-4 ring-primary/15',
                  !done && !active && 'border-border bg-card text-muted-foreground',
                )}
              >
                {done ? <Check className="size-4" aria-hidden /> : i + 1}
              </span>
              <span className={cn('h-0.5 flex-1', i === STAGE_ORDER.length - 1 ? 'opacity-0' : done ? 'bg-primary' : 'bg-border')} />
            </span>
            <span className={cn('text-xs leading-tight', active ? 'font-semibold text-foreground' : 'text-muted-foreground')}>
              {stageName(s, lang)}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
