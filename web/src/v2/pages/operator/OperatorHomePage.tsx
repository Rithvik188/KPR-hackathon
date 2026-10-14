import { ArrowRight, BellRing, FileText, MapPin, MessageSquareWarning, Newspaper, Store } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { useLang } from '@/i18n'
import { useAuth } from '@/v2/auth'
import { useNotices } from '@/v2/pages/operator/useNotices'

/** Operator home: same feature-card grid as the citizen home, with Notices in place of Track application. */
export function OperatorHomePage() {
  const { t } = useLang()
  const { profile } = useAuth()
  const operator = profile?.kind === 'operator' ? profile : null
  const { alerts } = useNotices(operator?.officeId)
  const open = alerts?.filter((a) => a.status === 'open').length ?? 0

  const features = [
    { to: '/operator/notices', icon: BellRing, title: t('v2.notices.title'), desc: t('v2.home.noticesDesc'), count: open },
    { to: '/operator/services', icon: FileText, title: t('v2.services.title'), desc: t('v2.operator.schemesDesc') },
    { to: '/operator/centres', icon: MapPin, title: t('v2.home.centres'), desc: t('v2.home.centresDesc') },
    { to: '/operator/news', icon: Newspaper, title: t('v2.home.news'), desc: t('v2.home.newsDesc') },
    {
      to: `/operator/report?office=${encodeURIComponent(operator?.officeId ?? '')}`,
      icon: MessageSquareWarning,
      title: t('v2.home.report'),
      desc: t('v2.home.reportDesc'),
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('v2.home.welcome', { name: operator?.name ?? '' })}</h1>
        <p className="text-muted-foreground">{t('v2.operator.subtitle')}</p>
      </div>

      {operator && (
        <Card className="py-0">
          <CardContent className="py-3">
            {/* CardContent is flex-col; the row lives in its own div */}
            <div className="flex flex-wrap items-center gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-accent text-primary">
                <Store className="size-5" aria-hidden />
              </span>
              <div className="min-w-0">
                <p className="font-medium">{operator.officeName}</p>
                <p className="font-mono text-xs text-muted-foreground">{operator.employeeId}</p>
              </div>
              <Badge className={`ml-auto ${operator.centreType === 'govt' ? 'bg-accent text-primary' : 'bg-secondary text-foreground'}`}>
                {t(operator.centreType === 'govt' ? 'v2.operator.centreGovt' : 'v2.operator.centrePrivate')}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(({ to, icon: Icon, title, desc, count }) => (
          <Link key={to} to={to} className="group block">
            <Card className="h-full transition-colors group-hover:border-primary/50">
              <CardContent className="flex h-full flex-col gap-3">
                <span className="flex size-11 items-center justify-center rounded-lg bg-accent text-primary">
                  <Icon className="size-5" aria-hidden />
                </span>
                <div className="flex-1">
                  <p className="flex items-center gap-2 font-medium">
                    {title}
                    {count ? <span className="rounded-full bg-danger px-2 text-xs text-white tabular-nums">{count}</span> : null}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
                </div>
                <span className="flex items-center gap-1 text-sm font-medium text-primary">
                  {title}
                  <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" aria-hidden />
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
