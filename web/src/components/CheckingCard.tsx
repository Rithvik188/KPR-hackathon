import { ScanLine } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useLang } from '@/i18n'

/** Placeholder shown while a document is being validated (quality path ~0.2 s, full OCR ~1–2 s). */
export function CheckingCard() {
  const { t } = useLang()
  return (
    <Card aria-busy="true" className="animate-in duration-200 fade-in">
      <CardContent className="space-y-3 py-2">
        <p className="flex items-center gap-2 text-sm font-medium text-primary">
          <ScanLine className="size-4 animate-pulse" aria-hidden />
          {t('counter.checking')}
        </p>
        <Skeleton className="h-6 w-28" />
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </CardContent>
    </Card>
  )
}
