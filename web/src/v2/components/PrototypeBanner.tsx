import { FlaskConical } from 'lucide-react'

import { useLang } from '@/i18n'

/** Non-negotiable guardrail: every v2 page carries this. Never remove it. */
export function PrototypeBanner() {
  const { t } = useLang()
  return (
    <div className="bg-warning-soft px-4 py-1.5 text-center text-xs font-medium text-warning">
      <FlaskConical className="mr-1 inline size-3.5 align-[-2px]" aria-hidden />
      {t('v2.prototypeBanner')}
    </div>
  )
}

export function TricolorRibbon() {
  return (
    <div className="flex h-1" aria-hidden="true">
      <div className="flex-1" style={{ background: 'var(--saffron)' }} />
      <div className="flex-1 bg-white" />
      <div className="flex-1" style={{ background: 'var(--tn-green)' }} />
    </div>
  )
}
