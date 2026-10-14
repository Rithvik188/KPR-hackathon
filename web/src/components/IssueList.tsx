import { CircleAlert, Info, TriangleAlert } from 'lucide-react'

import type { Audience, Issue, IssueSeverity } from '@/api/types'
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
