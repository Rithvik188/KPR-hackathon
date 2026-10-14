import { CircleAlert, Info, TriangleAlert } from 'lucide-react'

import type { Audience, Issue, IssueSeverity } from '@/api/types'
import { useLang } from '@/i18n'
import { issueLabel } from '@/lib/issues'
import { cn } from '@/lib/utils'

const SEVERITY_ORDER: Record<IssueSeverity, number> = { blocking: 0, warning: 1, info: 2 }

const SEVERITY_STYLE: Record<IssueSeverity, { Icon: typeof Info; className: string }> = {
  blocking: { Icon: CircleAlert, className: 'text-danger' },
  warning: { Icon: TriangleAlert, className: 'text-warning' },
  info: { Icon: Info, className: 'text-muted-foreground' },
}

/**
 * Bilingual issue list: Tamil large, English below. `audience="citizen"` (the counter) hides
 * officer-only issues; the officer view passes "officer" to see everything.
 */
export function IssueList({ issues, audience }: { issues: Issue[]; audience: Audience }) {
  const visible = issues
    .filter((i) => audience === 'officer' || i.audience === 'citizen')
    .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])
  if (visible.length === 0) return null

  return (
    <ul className="space-y-3">
      {visible.map((issue) => {
        const { Icon, className } = SEVERITY_STYLE[issue.severity]
        return (
          <li key={issue.code} className="flex gap-3">
            <Icon className={cn('mt-1 size-5 shrink-0', className)} aria-hidden />
            <div className="min-w-0">
              <p lang="ta" className="font-tamil text-lg leading-snug font-semibold">
                {issue.msg_ta}
              </p>
              <p lang="en" className="text-sm text-muted-foreground">
                {issue.msg_en}
              </p>
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function formatEvidence(value: unknown): string {
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(3).replace(/0+$/, '')
  if (typeof value === 'object' && value !== null) return JSON.stringify(value)
  return String(value)
}

/**
 * Officer view of issues: every audience, code label first, English then Tamil, and the measured evidence
 * (value vs threshold) behind an expander, so each flag is explainable.
 */
export function OfficerIssueList({ issues }: { issues: Issue[] }) {
  const { t } = useLang()
  const sorted = [...issues].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])
  if (sorted.length === 0) return null

  return (
    <ul className="space-y-2.5">
      {sorted.map((issue) => {
        const { Icon, className } = SEVERITY_STYLE[issue.severity]
        const evidence = Object.entries(issue.evidence ?? {})
        return (
          <li key={issue.code} className="flex gap-2.5">
            <Icon className={cn('mt-0.5 size-4 shrink-0', className)} aria-hidden />
            <div className="min-w-0 flex-1 space-y-0.5">
              <p className="text-sm">
                <span className="font-medium">{issueLabel(issue.code)}</span>
                <span className="ml-2 font-mono text-[11px] text-muted-foreground">{issue.code}</span>
              </p>
              <p className="text-sm text-muted-foreground">{issue.msg_en}</p>
              <p lang="ta" className="font-tamil text-xs text-muted-foreground">
                {issue.msg_ta}
              </p>
              {evidence.length > 0 && (
                <details className="group text-xs">
                  <summary className="cursor-pointer text-primary select-none hover:underline">{t('officer.evidence')}</summary>
                  <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 rounded-md bg-muted px-2.5 py-1.5 font-mono">
                    {evidence.map(([k, v]) => (
                      <div key={k} className="contents">
                        <dt className="text-muted-foreground">{k}</dt>
                        <dd className="break-all">{formatEvidence(v)}</dd>
                      </div>
                    ))}
                  </dl>
                </details>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
