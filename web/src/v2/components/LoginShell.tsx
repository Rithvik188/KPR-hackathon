import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useLang } from '@/i18n'
import { PortalFooter } from '@/v2/components/PortalFooter'
import { PrototypeBanner, TricolorRibbon } from '@/v2/components/PrototypeBanner'

type LoginKind = 'citizen' | 'department' | 'operator'

const LOGINS: { kind: LoginKind; to: string; label: 'v2.login.citizen' | 'v2.login.department' | 'v2.login.operator' }[] = [
  { kind: 'citizen', to: '/login', label: 'v2.login.citizen' },
  { kind: 'department', to: '/department-login', label: 'v2.login.department' },
  { kind: 'operator', to: '/operator-login', label: 'v2.login.operator' },
]

/** Shared frame for the three mock sign-in pages: prototype banner, title, card, links to the other sign-ins. */
export function LoginShell({
  current,
  icon: Icon,
  title,
  subtitle,
  children,
}: {
  current: LoginKind
  icon: LucideIcon
  title: string
  subtitle: string
  children: ReactNode
}) {
  const { t } = useLang()
  return (
    <div className="flex min-h-screen flex-col">
      <TricolorRibbon />
      <PrototypeBanner />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-10">
        <div className="mb-6 text-center">
          <span className="mx-auto flex size-14 items-center justify-center rounded-full" style={{ background: 'var(--primary)' }}>
            <Icon className="size-7 text-white" aria-hidden />
          </span>
          <h1 className="mt-3 text-xl font-semibold">{title}</h1>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t('v2.login.title')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {children}
            <p className="text-center text-xs text-muted-foreground">{t('v2.login.demoNotice')}</p>
          </CardContent>
        </Card>
        <nav aria-label={t('v2.login.otherLogins')} className="mt-4 flex flex-wrap justify-center gap-x-4 gap-y-1 text-sm">
          {LOGINS.filter((l) => l.kind !== current).map((l) => (
            <Link key={l.kind} to={l.to} className="text-primary hover:underline">
              {t('v2.login.switch', { kind: t(l.label) })}
            </Link>
          ))}
        </nav>
      </main>
      <PortalFooter />
    </div>
  )
}
