import { MessageSquareWarning } from 'lucide-react'

import type { IssueReport, Office } from '@/api/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useLang } from '@/i18n'
import { dateTime } from '@/lib/format'

export function ReportList({ reports, offices }: { reports: IssueReport[] | null; offices: Office[] }) {
  const { t } = useLang()
  const names = Object.fromEntries(offices.map((o) => [o.id, o.name]))
  if (reports === null) return <Skeleton className="h-24 w-full" />
  if (reports.length === 0) return <p className="text-sm text-muted-foreground">{t('report.none')}</p>
  return (
    <ul className="divide-y">
      {reports.map((r) => (
        <li key={r.id} className="flex gap-3 py-2.5">
          <MessageSquareWarning className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
          <div className="min-w-0 space-y-0.5">
            <p className="text-sm">
              <span className="font-medium">{t(`category.${r.category}`)}</span>
              <span className="text-muted-foreground"> · {names[r.office_id] ?? r.office_id}</span>
            </p>
            <p className="text-sm text-muted-foreground">“{r.description}”</p>
            <p className="text-xs text-muted-foreground">
              {t(`role.${r.reporter_role}`)} · {dateTime(r.created_at)}
            </p>
          </div>
        </li>
      ))}
    </ul>
  )
}

export function RecentReports({ reports, offices }: { reports: IssueReport[] | null; offices: Office[] }) {
  const { t } = useLang()
  return (
    <Card className="gap-3">
      <CardHeader>
        <CardTitle className="text-base">{t('admin.reports')}</CardTitle>
      </CardHeader>
      <CardContent className="max-h-[360px] overflow-y-auto">
        <ReportList reports={reports} offices={offices} />
      </CardContent>
    </Card>
  )
}
