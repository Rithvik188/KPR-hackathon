import { gsap } from 'gsap'
import { Building2, ShieldCheck } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useLang } from '@/i18n'
import { PortalFooter } from '@/v2/components/PortalFooter'
import { PrototypeBanner, TricolorRibbon } from '@/v2/components/PrototypeBanner'

/** Splash: emblem + title + "powered by SevaiCheck", then Continue → citizen login. */
export function LandingPage() {
  const { t } = useLang()
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const root = rootRef.current
    if (!root) return
    if (reduced) {
      gsap.set(root.querySelectorAll('[data-reveal]'), { opacity: 1, y: 0, scale: 1 })
      return
    }
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: 'power2.out' } })
      tl.from('[data-reveal="emblem"]', { opacity: 0, scale: 0.85, duration: 0.5 })
        .from('[data-reveal="title"]', { opacity: 0, y: 16, duration: 0.4 }, '-=0.2')
        .from('[data-reveal="tagline"]', { opacity: 0, y: 12, duration: 0.4 }, '-=0.2')
        .from('[data-reveal="cta"]', { opacity: 0, y: 12, duration: 0.35 }, '-=0.2')
    }, root)
    return () => ctx.revert()
  }, [])

  return (
    <div ref={rootRef} className="flex min-h-screen flex-col">
      <TricolorRibbon />
      <PrototypeBanner />
      <main className="mx-auto flex w-full max-w-lg flex-1 flex-col items-center justify-center px-4 py-16 text-center">
        <span
          data-reveal="emblem"
          className="flex size-24 items-center justify-center rounded-full shadow-sm"
          style={{ background: 'var(--primary)' }}
        >
          <Building2 className="size-12 text-white" aria-hidden />
        </span>
        <div data-reveal="title" className="mt-6">
          <p className="font-tamil text-lg text-muted-foreground">தமிழ்நாடு அரசு</p>
          <h1 className="text-3xl font-semibold tracking-tight">{t('v2.landing.title')}</h1>
        </div>
        <p data-reveal="tagline" className="mt-2 text-muted-foreground">
          {t('v2.landing.tagline')}
        </p>
        <p data-reveal="tagline" className="mt-1 text-sm font-medium text-primary">
          {t('v2.poweredBy')}
        </p>
        <div data-reveal="cta" className="mt-8">
          <Button asChild size="lg" className="px-10">
            <Link to="/login">
              <ShieldCheck aria-hidden />
              {t('v2.landing.continue')}
            </Link>
          </Button>
        </div>
      </main>
      <PortalFooter />
    </div>
  )
}
