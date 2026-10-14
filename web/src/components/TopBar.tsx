import { ShieldCheck } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { USE_FIXTURES } from '@/api/client'
import { type I18nKey, useLang } from '@/i18n'
import { cn } from '@/lib/utils'

const NAV: { to: string; key: I18nKey }[] = [
  { to: '/counter', key: 'nav.counter' },
  { to: '/officer', key: 'nav.officer' },
  { to: '/admin', key: 'nav.admin' },
  { to: '/metrics', key: 'nav.metrics' },
  { to: '/report', key: 'nav.report' },
]

function LangToggle() {
  const { lang, setLang } = useLang()
  const option = (value: 'en' | 'ta', label: string) => (
    <button
      type="button"
      onClick={() => setLang(value)}
      aria-pressed={lang === value}
      className={cn(
        'rounded-md px-2.5 py-1 text-sm transition-colors',
        lang === value ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground',
      )}
    >
      {label}
    </button>
  )
  return (
    <div className="flex shrink-0 rounded-lg border bg-background p-0.5" role="group" aria-label="Language">
      {option('en', 'EN')}
      {option('ta', 'தமிழ்')}
    </div>
  )
}

export function TopBar() {
  const { t } = useLang()
  return (
    <header className="sticky top-0 z-40 border-b bg-card/95 backdrop-blur">
      {/* Phone: logo + language on row 1, scrollable nav on row 2. md and up: one row. */}
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-1 px-4 pt-2 md:h-14 md:flex-nowrap md:py-0">
        <NavLink to="/counter" className="flex shrink-0 items-center gap-2 font-semibold text-primary">
          <ShieldCheck className="size-5" aria-hidden />
          <span className="text-lg tracking-tight">SevaiCheck</span>
        </NavLink>
        <nav
          className="no-scrollbar order-last -mx-1 flex w-full gap-1 overflow-x-auto pb-2 md:order-none md:mx-0 md:w-auto md:min-w-0 md:flex-1 md:pb-0"
          aria-label="Main"
        >
          {NAV.map(({ to, key }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'rounded-md px-3 py-1.5 text-sm whitespace-nowrap transition-colors',
                  isActive ? 'bg-accent font-medium text-accent-foreground' : 'text-muted-foreground hover:text-foreground',
                )
              }
            >
              {t(key)}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          {USE_FIXTURES && (
            <span className="hidden rounded bg-warning-soft px-2 py-0.5 text-xs font-medium text-warning sm:inline">
              FIXTURE MODE
            </span>
          )}
          <LangToggle />
        </div>
      </div>
    </header>
  )
}
