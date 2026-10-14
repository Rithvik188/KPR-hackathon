import { ArrowRight, FileText, MapPin, MessageSquareWarning, Newspaper, Search } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Card, CardContent } from '@/components/ui/card'
import { useLang } from '@/i18n'
import { useAuth } from '@/v2/auth'

const FEATURES = [
  { to: '/portal/services', icon: FileText, title: 'v2.home.applyServices', desc: 'v2.home.applyServicesDesc' },
  { to: '/portal/track', icon: Search, title: 'v2.home.track', desc: 'v2.home.trackDesc' },
  { to: '/portal/centres', icon: MapPin, title: 'v2.home.centres', desc: 'v2.home.centresDesc' },
  { to: '/portal/news', icon: Newspaper, title: 'v2.home.news', desc: 'v2.home.newsDesc' },
  { to: '/portal/report', icon: MessageSquareWarning, title: 'v2.home.report', desc: 'v2.home.reportDesc' },
] as const

/** Citizen home: welcome + the portal's features only. Document upload never appears here — only after a
 * service is picked on the Apply flow. */
export function HomePage() {
  const { t } = useLang()
  const { profile } = useAuth()
  const name = profile?.kind === 'citizen' ? profile.name : ''

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('v2.home.welcome', { name })}</h1>
        <p className="text-muted-foreground">{t('v2.home.subtitle')}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(({ to, icon: Icon, title, desc }) => (
          <Link key={to} to={to} className="group block">
            <Card className="h-full transition-colors group-hover:border-primary/50">
              <CardContent className="flex h-full flex-col gap-3">
                <span className="flex size-11 items-center justify-center rounded-lg bg-accent text-primary">
                  <Icon className="size-5" aria-hidden />
                </span>
                <div className="flex-1">
                  <p className="font-medium">{t(title)}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{t(desc)}</p>
                </div>
                <span className="flex items-center gap-1 text-sm font-medium text-primary">
                  {t(title)}
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
