import { Hammer } from 'lucide-react'

import { useLang } from '@/i18n'

export function ComingSoon({ title }: { title: string }) {
  const { t } = useLang()
  return (
    <div className="mx-auto max-w-xl rounded-xl border border-dashed bg-card p-10 text-center">
      <Hammer className="mx-auto mb-3 size-8 text-muted-foreground" aria-hidden />
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="text-muted-foreground">{t('common.comingSoon')}</p>
    </div>
  )
}
