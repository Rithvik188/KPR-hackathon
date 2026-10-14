import { Camera, Timer } from 'lucide-react'

import type { DocFields, ValidationResult } from '@/api/types'
import { IssueList } from '@/components/IssueList'
import { DocStatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { type I18nKey, useLang } from '@/i18n'
import { isoDateToDisplay, seconds } from '@/lib/format'

const FIELD_ORDER = ['id_number_display', 'name', 'dob', 'gender', 'father_name', 'pin_code'] as const

function FieldGrid({ fields }: { fields: DocFields }) {
  const { t } = useLang()
  const rows = FIELD_ORDER.filter((k) => fields[k])
  if (rows.length === 0) return null
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
      {rows.map((key) => (
        <div key={key} className="contents">
          <dt className="text-muted-foreground">{t(`field.${key}` as I18nKey)}</dt>
          <dd className="font-medium tabular-nums">{key === 'dob' ? isoDateToDisplay(fields[key]) : fields[key]}</dd>
        </div>
      ))}
    </dl>
  )
}

/** The counter's answer for one upload: status, bilingual issues, retake, latency and read fields. */
export function ResultCard({ result, onRetake }: { result: ValidationResult; onRetake?: () => void }) {
  const { t } = useLang()
  const accepted = result.status === 'accepted'

  return (
    <Card className="animate-in duration-200 fade-in slide-in-from-bottom-1">
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
        <DocStatusBadge status={result.status} />
        <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs text-muted-foreground">
          <Timer className="size-3.5" aria-hidden />
          {t('counter.checkedIn', { s: seconds(result.timings_ms.total) })}
        </span>
      </CardHeader>
      <CardContent className="space-y-4">
        <IssueList issues={result.issues} audience="citizen" />
        {accepted && result.fields && (
          <div className="space-y-2">
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{t('counter.fields')}</p>
            <FieldGrid fields={result.fields} />
          </div>
        )}
        {!accepted && onRetake && (
          <Button size="lg" onClick={onRetake} className="w-full sm:w-auto">
            <Camera aria-hidden />
            {t('counter.retake')}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
