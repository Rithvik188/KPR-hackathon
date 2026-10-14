import { Building2, LogOut, UserRound } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useLang } from '@/i18n'
import { PrototypeBanner, TricolorRibbon } from '@/v2/components/PrototypeBanner'
import { useAuth } from '@/v2/auth'

function LangToggle() {
  const { lang, setLang } = useLang()
  const option = (value: 'en' | 'ta', label: string) => (
    <button
      type="button"
      onClick={() => setLang(value)}
      aria-pressed={lang === value}
      className={`rounded-md px-2.5 py-1 text-sm transition-colors ${
        lang === value ? 'bg-white text-primary' : 'text-white/85 hover:text-white'
      }`}
    >
      {label}
    </button>
  )
  return (
    <div className="flex shrink-0 rounded-lg border border-white/30 p-0.5" role="group" aria-label="Language">
      {option('en', 'EN')}
      {option('ta', 'தமிழ்')}
    </div>
  )
}

/** Header for every citizen-portal page: emblem, bilingual title, language toggle, profile/logout. */
export function PortalHeader({
  homeHref = '/portal',
  nav,
}: {
  homeHref?: string
  nav?: { to: string; label: string }[]
}) {
  const { t } = useLang()
  const { profile, logout } = useAuth()

  return (
    <header className="sticky top-0 z-40">
      <TricolorRibbon />
      <div style={{ background: 'var(--primary)' }} className="text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-2.5">
          <Link to={homeHref} className="flex shrink-0 items-center gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-white text-primary">
              <Building2 className="size-5" aria-hidden />
            </span>
            <span className="leading-tight">
              <span className="block font-tamil text-sm font-medium">தமிழ்நாடு அரசு</span>
              <span className="block text-[15px] font-medium tracking-tight">TN e-Sevai</span>
              <span className="block text-[11px] text-white/75">{t('v2.poweredBy')}</span>
            </span>
          </Link>
          {nav && (
            <nav className="order-last flex w-full gap-1 overflow-x-auto sm:order-none sm:w-auto sm:flex-1" aria-label="Main">
              {nav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === homeHref}
                  className={({ isActive }) =>
                    `shrink-0 rounded-md px-3 py-1.5 text-sm whitespace-nowrap transition-colors ${
                      isActive ? 'bg-white/15 font-medium text-white' : 'text-white/80 hover:text-white'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          )}
          <div className="ml-auto flex items-center gap-2">
            <LangToggle />
            {profile && (
              <div className="flex items-center gap-1.5 text-sm">
                <span className="hidden items-center gap-1.5 rounded-md bg-white/10 px-2.5 py-1.5 sm:flex">
                  <UserRound className="size-4" aria-hidden />
                  {profile.name}
                </span>
                <Button size="icon" variant="ghost" className="text-white hover:bg-white/15 hover:text-white" onClick={logout} aria-label={t('v2.logout')}>
                  <LogOut className="size-4" aria-hidden />
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
      <PrototypeBanner />
    </header>
  )
}
