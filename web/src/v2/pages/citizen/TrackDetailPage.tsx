import { useEffect, useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { getApplication, listNotifications } from '@/api/client'
import type { ApplicationDetail, Notification } from '@/api/types'
import { ConsistencyCard } from '@/components/ConsistencyCard'
import { FlagChips } from '@/components/FlagChips'
import { StageTrack } from '@/components/StageTrack'
import { AppStatusBadge, DocStatusBadge } from '@/components/StatusBadge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useLang } from '@/i18n'
import { dateTime } from '@/lib/format'
import { trackedApplicationIds } from '@/v2/data/tracked'
import { Breadcrumbs } from '@/v2/components/Breadcrumbs'

export function TrackDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { t } = useLang()
  const [detail, setDetail] = useState<ApplicationDetail | null>(null)
  const [notifications, setNotifications] = useState<Notification[]>([])

  useEffect(() => {
    if (!id) return
    getApplication(id)
      .then(setDetail)
      .catch((err) => toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) }))
    listNotifications(id)
      .then(setNotifications)
      .catch(() => {})
  }, [id, t])

  if (!id || !trackedApplicationIds().includes(id)) return <Navigate to="/portal/track" replace />

  return (
    <div className="space-y-5">
      <Breadcrumbs items={[{ label: t('v2.home.track'), to: '/portal/track' }, { label: id }]} />
      {!detail ? (
        <div className="space-y-3">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">{t('v2.track.detail.title', { id: detail.id })}</h1>
              <p className="text-muted-foreground">{dateTime(detail.created_at)}</p>
            </div>
            <AppStatusBadge status={detail.status} />
          </div>

          {detail.flag_codes.length > 0 && <FlagChips codes={detail.flag_codes} />}

          {(detail.stage || detail.status === 'approved') && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t('v2.track.detail.chain')}</CardTitle>
              </CardHeader>
              <CardContent>
                <StageTrack stage={detail.stage} status={detail.status} />
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-base">{t('v2.track.detail.documents')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {detail.documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between gap-2 rounded-md border px-3 py-2">
                  <span className="text-sm">{t(`doc.${(doc.declared_type ?? doc.doc_type) as never}`)}</span>
                  <DocStatusBadge status={doc.status} />
                </div>
              ))}
            </CardContent>
          </Card>

          <ConsistencyCard consistency={detail.consistency} />

          <Card>
            <CardHeader>
              <CardTitle className="text-base">{t('v2.track.detail.timeline')}</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="relative space-y-3 border-l pl-4">
                {detail.history.map((h, i) => (
                  <li key={i} className="relative">
                    <span className="absolute top-1.5 -left-[21px] size-2.5 rounded-full border-2 border-card bg-primary" />
                    <p className="text-sm">
                      <span className="font-medium">{h.event.replaceAll('_', ' ')}</span>
                      <span className="ml-2 text-xs text-muted-foreground">{dateTime(h.at)}</span>
                    </p>
                    {h.note && <p className="text-xs text-muted-foreground">{h.note}</p>}
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>

          {notifications.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t('v2.track.detail.notifications')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {notifications.map((n) => (
                  <div key={n.id} className="rounded-md bg-muted p-3">
                    <p lang="ta" className="font-tamil text-sm">
                      {n.body_ta}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">{n.body_en}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
