import { issueLabel } from '@/lib/issues'
import { cn } from '@/lib/utils'

// Officer-facing warnings (do not block the application); everything else in flag_codes is blocking.
const WARNING_CODES = new Set(['DUPLICATE_SUSPECTED', 'NAME_LIKELY_MATCH'])

export function FlagChips({ codes, className }: { codes: string[]; className?: string }) {
  if (codes.length === 0) return <span className="text-muted-foreground">—</span>
  return (
    <div className={cn('flex flex-wrap gap-1', className)}>
      {codes.map((code) => (
        <span
          key={code}
          title={code}
          className={cn(
            'rounded px-1.5 py-0.5 text-[11px] font-medium whitespace-nowrap',
            WARNING_CODES.has(code) ? 'bg-warning-soft text-warning' : 'bg-danger-soft text-danger',
          )}
        >
          {issueLabel(code)}
        </span>
      ))}
    </div>
  )
}
