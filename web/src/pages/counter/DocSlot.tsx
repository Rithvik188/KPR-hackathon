import { ChevronRight } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { uploadDocument } from '@/api/client'
import type { DeclarableType, DocStatus, SupportingType, UploadResult, ValidationResult } from '@/api/types'
import { CheckingCard } from '@/components/CheckingCard'
import { LatencyChip, ResultBody } from '@/components/ResultCard'
import { DocStatusBadge } from '@/components/StatusBadge'
import { UploadBox } from '@/components/UploadBox'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useLang } from '@/i18n'
import { cn } from '@/lib/utils'

export type SlotName = 'aadhaar_front' | 'aadhaar_back' | 'id_proof' | 'supporting'

interface Attempt {
  status: DocStatus
  codes: string[]
}

function AttemptHistory({ attempts }: { attempts: Attempt[] }) {
  const { t } = useLang()
  if (attempts.length < 2) return null
  return (
    <ol className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground" aria-label="Attempts">
      {attempts.map((a, i) => (
        <li key={i} className="flex items-center gap-1">
          {i > 0 && <ChevronRight className="size-3" aria-hidden />}
          <span>{t('counter.attempt', { n: i + 1 })}:</span>
          <span
            className={cn(
              'font-medium',
              a.status === 'accepted' ? 'text-success' : a.status === 'invalid' ? 'text-danger' : 'text-warning',
            )}
          >
            {a.status === 'accepted' ? t('status.accepted') : a.codes.join(', ') || t(`status.${a.status}`)}
          </span>
        </li>
      ))}
    </ol>
  )
}

/** One required document slot: upload, bilingual result, retake, and the attempt history. */
export function DocSlot({
  slot,
  applicationId,
  onUploaded,
  supportingType,
}: {
  slot: SlotName
  applicationId: string | null
  onUploaded: (result: UploadResult) => void
  /** Required when slot === 'supporting': the document this service needs (from contract/services.json). */
  supportingType?: SupportingType | null
}) {
  const { t } = useLang()
  const [idType, setIdType] = useState<'pan' | 'voter_id'>('pan')
  const [busy, setBusy] = useState(false)
  const [latest, setLatest] = useState<ValidationResult | null>(null)
  const [attempts, setAttempts] = useState<Attempt[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const declaredType = (slot === 'id_proof' ? idType : slot === 'supporting' ? supportingType : slot) as DeclarableType
  const title =
    slot === 'id_proof'
      ? `${t('counter.idProof')} · ${t(`doc.${idType}`)}`
      : slot === 'supporting'
        ? t(`doc.${supportingType ?? 'unknown'}`)
        : t(`doc.${slot}`)

  async function upload(file: File) {
    if (!applicationId || !declaredType) return
    setBusy(true)
    try {
      const res = await uploadDocument(applicationId, file, declaredType)
      const v = res.validation
      setLatest(v)
      setAttempts((prev) => [
        ...prev,
        { status: v.status, codes: v.issues.filter((i) => i.severity === 'blocking').map((i) => i.code) },
      ])
      onUploaded(res)
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setBusy(false)
    }
  }

  const accepted = latest?.status === 'accepted'

  return (
    <Card className={cn('gap-4 transition-colors', accepted && 'border-success/40')}>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          {latest && <LatencyChip ms={latest.timings_ms.total} />}
          {latest && <DocStatusBadge status={latest.status} />}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {slot === 'id_proof' && !accepted && (
          <div className="inline-flex rounded-lg border bg-background p-0.5" role="group" aria-label={t('counter.idProof')}>
            {(['pan', 'voter_id'] as const).map((type) => (
              <button
                key={type}
                type="button"
                aria-pressed={idType === type}
                onClick={() => setIdType(type)}
                className={cn(
                  'rounded-md px-3 py-1 text-sm transition-colors',
                  idType === type ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {t(`doc.${type}`)}
              </button>
            ))}
          </div>
        )}
        {slot === 'supporting' && <p className="text-xs text-muted-foreground">{t('counter.verifiedByOfficer')}</p>}
        <AttemptHistory attempts={attempts} />
        {busy ? (
          <CheckingCard />
        ) : latest ? (
          <ResultBody result={latest} onRetake={() => inputRef.current?.click()} />
        ) : (
          <UploadBox onFile={upload} disabled={!applicationId || !declaredType} inputRef={inputRef} compact />
        )}
        {/* Keep a hidden input mounted after a result so Retake can reopen the camera / picker. */}
        {latest && !busy && (
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png"
            capture="environment"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              e.target.value = ''
              if (file) upload(file)
            }}
          />
        )}
      </CardContent>
    </Card>
  )
}
