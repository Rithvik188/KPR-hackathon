import { useLang } from '@/i18n'

export function PortalFooter() {
  const { t } = useLang()
  return (
    <footer className="mt-12 border-t bg-card">
      <div className="mx-auto max-w-7xl px-4 py-6 text-center text-xs text-muted-foreground">
        <p>{t('v2.footerPrototype')}</p>
        <p className="mt-1">{t('v2.poweredBy')} · SevaiCheck</p>
      </div>
    </footer>
  )
}
