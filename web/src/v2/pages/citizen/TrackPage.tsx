import { FileText, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getApplication } from '@/api/client'
import type { ApplicationDetail } from '@/api/types'
import { AppStatusBadge } from '@/components/StatusBadge'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useLang } from '@/i18n'
import { dateTime } from '@/lib/format'
import { Breadcrumbs } from '@/v2/components/Breadcrumbs'
import { SCHEMES } from '@/v2/data/schemes'
import { trackedApplicationIds } from '@/v2/data/tracked'

export function TrackPage() {
  const { t, lang } = useLang()
  const [apps, setApps] = useState<ApplicationDetail[] | null>(null)

  useEffect(() => {
    const ids = trackedApplicationIds()
    if (ids.length === 0) {
      setApps([])
      return
    }
    Promise.all(ids.map((id) => getApplication(id).catch(() => null))).then((list) =>
      setApps(list.filter((a): a is ApplicationDetail => a !== null)),
    )
  }, [])

  return (
    <div className="space-y-5">
      <Breadcrumbs items={[{ label: t('v2.home.track') }]} />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('v2.track.title')}</h1>
        <p className="text-muted-foreground">{t('v2.track.subtitle')}</p>
      </div>

      {apps === null && (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}
      {apps?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <Search className="size-8 text-muted-foreground" aria-hidden />
            <p className="text-muted-foreground">{t('v2.track.empty')}</p>
            <Link to="/portal/services" className="text-sm font-medium text-primary hover:underline">
              {t('v2.track.emptyCta')}
            </Link>
          </CardContent>
        </Card>
      )}
      <div className="space-y-3">
        {apps?.map((app) => {
          const scheme = SCHEMES.find((s) => s.service === app.service)
          return (
            <Link key={app.id} to={`/portal/track/${app.id}`}>
              <Card className="transition-colors hover:border-primary/40">
                <CardContent className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="flex size-10 items-center justify-center rounded-lg bg-accent text-primary">
                      <FileText className="size-5" aria-hidden />
                    </span>
                    <div>
                      <p className="font-medium">{scheme ? (lang === 'ta' ? scheme.nameTa : scheme.nameEn) : app.service}</p>
                      <p className="font-mono text-xs text-muted-foreground">
                        {app.id}
                        {app.can_id ? ` · ${app.can_id}` : ''} · {dateTime(app.created_at)}
                      </p>
                    </div>
                  </div>
                  <AppStatusBadge status={app.status} />
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
