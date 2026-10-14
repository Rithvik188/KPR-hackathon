// Counter v1 (P2-1): a single upload box against POST /api/validate. P2-2 replaces this with the
// full application flow (operator bar, three document slots, application panel, phone mock).
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { setValidateFixture, USE_FIXTURES, validateDocument, type ValidateFixture } from '@/api/client'
import type { DeclarableType, ValidationResult } from '@/api/types'
import { CheckingCard } from '@/components/CheckingCard'
import { ResultCard } from '@/components/ResultCard'
import { UploadBox } from '@/components/UploadBox'
import { Card, CardContent } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useLang } from '@/i18n'

const DOC_TYPES: DeclarableType[] = ['aadhaar_front', 'aadhaar_back', 'pan', 'voter_id']

export function CounterPage() {
  const { t } = useLang()
  const [declaredType, setDeclaredType] = useState<DeclarableType>('aadhaar_front')
  const [checking, setChecking] = useState(false)
  const [result, setResult] = useState<ValidationResult | null>(null)
  const [fixtureChoice, setFixtureChoice] = useState<ValidateFixture>('fixable')
  const inputRef = useRef<HTMLInputElement>(null)

  async function check(file: File) {
    setChecking(true)
    setResult(null)
    try {
      setResult(await validateDocument(file, declaredType))
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('counter.title')}</h1>
        <p className="text-muted-foreground">{t('counter.subtitle')}</p>
      </div>

      <Card>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="doc-type">{t('counter.docType')}</Label>
              <Select value={declaredType} onValueChange={(v) => setDeclaredType(v as DeclarableType)}>
                <SelectTrigger id="doc-type" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DOC_TYPES.map((d) => (
                    <SelectItem key={d} value={d}>
                      {t(`doc.${d}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {USE_FIXTURES && (
              // DEBUG (fixture mode only): pick which validate fixture the upload returns. Remove in P2-4.
              <div className="space-y-1.5">
                <Label htmlFor="fixture">{t('counter.debugFixture')}</Label>
                <Select
                  value={fixtureChoice}
                  onValueChange={(v) => {
                    setFixtureChoice(v as ValidateFixture)
                    setValidateFixture(v as ValidateFixture)
                  }}
                >
                  <SelectTrigger id="fixture" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fixable">validate_fixable</SelectItem>
                    <SelectItem value="accepted">validate_accepted</SelectItem>
                    <SelectItem value="invalid">validate_invalid</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          <UploadBox onFile={check} disabled={checking} inputRef={inputRef} />
        </CardContent>
      </Card>

      {checking && <CheckingCard />}
      {result && !checking && <ResultCard result={result} onRetake={() => inputRef.current?.click()} />}
    </div>
  )
}
