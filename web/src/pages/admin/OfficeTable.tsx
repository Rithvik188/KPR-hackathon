import { ArrowDown, ArrowUp } from 'lucide-react'
import { useState } from 'react'

import type { OperationsMetrics } from '@/api/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { type I18nKey, useLang } from '@/i18n'
import { percent } from '@/lib/format'
import { issueLabel } from '@/lib/issues'

type Row = OperationsMetrics['by_office'][number]
type SortKey = 'office_name' | 'taluk' | 'submissions' | 'reject_rate' | 'backlog'

const COLUMNS: { key: SortKey; label: I18nKey; numeric?: boolean }[] = [
  { key: 'office_name', label: 'officer.office' },
  { key: 'taluk', label: 'admin.taluk' },
  { key: 'submissions', label: 'admin.submissions', numeric: true },
  { key: 'reject_rate', label: 'admin.rejectRate', numeric: true },
  { key: 'backlog', label: 'admin.kpi.backlog', numeric: true },
]

export function OfficeTable({ rows }: { rows: Row[] | null }) {
  const { t } = useLang()
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: 'reject_rate', desc: true })
  const sorted = [...(rows ?? [])].sort((a, b) => {
    const x = a[sort.key]
    const y = b[sort.key]
    const cmp = typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y))
    return sort.desc ? -cmp : cmp
  })
  const maxRate = Math.max(0.01, ...sorted.map((r) => r.reject_rate))

  return (
    <Card className="gap-3">
      <CardHeader>
        <CardTitle className="text-base">{t('admin.offices')}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              {COLUMNS.map((c) => (
                <TableHead key={c.key} className={c.numeric ? 'text-right' : c.key === 'taluk' ? 'hidden xl:table-cell' : undefined}>
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 hover:text-foreground"
                    onClick={() => setSort((s) => ({ key: c.key, desc: s.key === c.key ? !s.desc : !!c.numeric }))}
                    aria-sort={sort.key === c.key ? (sort.desc ? 'descending' : 'ascending') : undefined}
                  >
                    {t(c.label)}
                    {sort.key === c.key && (sort.desc ? <ArrowDown className="size-3" /> : <ArrowUp className="size-3" />)}
                  </button>
                </TableHead>
              ))}
              <TableHead>{t('admin.topIssue')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((r) => (
              <TableRow key={r.office_id}>
                <TableCell className="font-medium">{r.office_name}</TableCell>
                <TableCell className="hidden text-muted-foreground xl:table-cell">{r.taluk}</TableCell>
                <TableCell className="text-right tabular-nums">{r.submissions}</TableCell>
                <TableCell className="text-right">
                  <span className="inline-flex items-center justify-end gap-2">
                    <span className="hidden h-1.5 w-16 overflow-hidden rounded-full bg-muted sm:inline-block">
                      <span className="block h-full rounded-full bg-[var(--series-1)]" style={{ width: `${(r.reject_rate / maxRate) * 100}%` }} />
                    </span>
                    <span className="tabular-nums">{percent(r.reject_rate, 1)}</span>
                  </span>
                </TableCell>
                <TableCell className="text-right tabular-nums">{r.backlog}</TableCell>
                <TableCell className="text-muted-foreground">{r.top_issue ? issueLabel(r.top_issue) : '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
