import { CircleCheckBig, ExternalLink, MessageSquareWarning } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { ApplicationSummary, ConsistencyResult } from '@/api/types'
import { ConsistencyCard } from '@/components/ConsistencyCard'
import { IssueList } from '@/components/IssueList'
import { AppStatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useLang } from '@/i18n'

/** Right-hand panel: application status, cross-document consistency and the "Sent to officer" moment. */
export function ApplicationPanel({
  application,
  consistency,
}: {
  application: ApplicationSummary
  consistency: ConsistencyResult | null
}) {
  const { t } = useLang()
  const ready = application.status === 'ready_for_officer'
  const appIssues = consistency?.issues.filter((i) => i.audience === 'citizen') ?? []

  return (
    <Card className="gap-4">
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="text-base">
          {t('counter.application')} <span className="font-mono text-sm text-muted-foreground">{application.id}</span>
        </CardTitle>
        <AppStatusBadge status={application.status} />
      </CardHeader>
      <CardContent className="space-y-4">
        {ready && (
          <div className="animate-in rounded-lg bg-success p-4 text-white duration-300 fade-in zoom-in-95">
            <p className="flex items-center gap-2 text-lg font-semibold">
              <CircleCheckBig className="size-6" aria-hidden />
              {t('counter.sentToOfficer')}
            </p>
            <p className="mt-1 text-sm text-white/90">{t('counter.sentToOfficerHint')}</p>
            <Button asChild variant="secondary" size="sm" className="mt-3">
              <Link to={`/officer?app=${encodeURIComponent(application.id)}`}>
                <ExternalLink aria-hidden />
                {t('counter.openInOfficer')}
              </Link>
            </Button>
          </div>
        )}
        {consistency && <ConsistencyCard consistency={consistency} />}
        {appIssues.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{t('counter.appIssues')}</p>
            <IssueList issues={appIssues} audience="citizen" />
          </div>
        )}
        <Link
          to={`/report?office=${encodeURIComponent(application.office_id)}`}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary"
        >
          <MessageSquareWarning className="size-4" aria-hidden />
          {t('counter.reportProblem')}
        </Link>
      </CardContent>
    </Card>
  )
}
