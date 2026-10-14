// Apply flow, scoped to the service chosen on the Schemes page. Document upload never appears before this
// point: step 1 collects the citizen's details and centre, step 2 uploads exactly this service's required
// documents (Aadhaar front+back + one ID proof + the service's supporting document), step 3 submits.
import { CheckCircle2, CircleCheck, ExternalLink, FileWarning, Send } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { createApplication, getOffices, uploadDocument } from '@/api/client'
import type { ApplicationSummary, ConsistencyResult, DeclarableType, Office, Service, UploadResult } from '@/api/types'
import { ConsistencyCard } from '@/components/ConsistencyCard'
import { ResultBody } from '@/components/ResultCard'
import { DocStatusBadge } from '@/components/StatusBadge'
import { UploadBox } from '@/components/UploadBox'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useLang } from '@/i18n'
import { supportingTypeFor } from '@/lib/services'
import { cn } from '@/lib/utils'
import { Breadcrumbs } from '@/v2/components/Breadcrumbs'
import { useAuth } from '@/v2/auth'
import { OPEN_SERVICES, SCHEMES } from '@/v2/data/schemes'
import { rememberApplication } from '@/v2/data/tracked'

const SERVICE_SLOTS = ['aadhaar_front', 'aadhaar_back', 'id_proof', 'supporting'] as const
type SlotName = (typeof SERVICE_SLOTS)[number]

function ApplySlot({
  slot,
  applicationId,
  supportingType,
  onUploaded,
}: {
  slot: SlotName
  applicationId: string
  supportingType: ReturnType<typeof supportingTypeFor>
  onUploaded: (result: UploadResult) => void
}) {
  const { t } = useLang()
  const [idType, setIdType] = useState<'pan' | 'voter_id'>('pan')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<UploadResult['validation'] | null>(null)
  const declaredType = (slot === 'id_proof' ? idType : slot === 'supporting' ? supportingType : slot) as DeclarableType
  const title = slot === 'id_proof' ? t('counter.idProof') : slot === 'supporting' ? t(`doc.${supportingType ?? 'unknown'}`) : t(`doc.${slot}`)

  async function upload(file: File) {
    if (!declaredType) return
    setBusy(true)
    try {
      const res = await uploadDocument(applicationId, file, declaredType)
      setResult(res.validation)
      onUploaded(res)
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setBusy(false)
    }
  }

  const accepted = result?.status === 'accepted'

  return (
    <Card className={cn('gap-3', accepted && 'border-success/40')}>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="text-base">{title}</CardTitle>
        {result && <DocStatusBadge status={result.status} />}
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
        {busy ? (
          <p className="text-sm text-muted-foreground">{t('counter.checking')}</p>
        ) : result ? (
          <ResultBody result={result} onRetake={() => document.getElementById(`apply-file-${slot}`)?.click()} />
        ) : (
          <UploadBox onFile={upload} disabled={!declaredType} />
        )}
        {result && !busy && (
          <input
            id={`apply-file-${slot}`}
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

export function ApplyPage() {
  const { service } = useParams<{ service: string }>()
  const { t, lang } = useLang()
  const { profile } = useAuth()
  const [offices, setOffices] = useState<Office[]>([])
  const [officeId, setOfficeId] = useState('')
  const [application, setApplication] = useState<ApplicationSummary | null>(null)
  const [consistency, setConsistency] = useState<ConsistencyResult | null>(null)
  const [accepted, setAccepted] = useState<Set<SlotName>>(new Set())
  const [submitted, setSubmitted] = useState(false)
  const [busy, setBusy] = useState(false)

  const scheme = SCHEMES.find((s) => s.service === service)
  const supportingType = service ? supportingTypeFor(service as Service) : null
  const slots: SlotName[] = supportingType ? [...SERVICE_SLOTS] : ['aadhaar_front', 'aadhaar_back', 'id_proof']

  useEffect(() => {
    getOffices().then(setOffices).catch(() => {})
  }, [])

  if (!service || !OPEN_SERVICES.has(service as Service) || !scheme) {
    return <Navigate to="/portal/services" replace />
  }

  async function start(e: FormEvent) {
    e.preventDefault()
    if (profile?.kind !== 'citizen' || !officeId) return
    setBusy(true)
    try {
      const app = await createApplication({
        citizen_name: profile.name,
        phone: profile.phone,
        service: service as Service,
        office_id: officeId,
        citizen_dob: profile.dob,
      })
      setApplication(app)
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setBusy(false)
    }
  }

  function onUploaded(slot: SlotName, res: UploadResult) {
    setApplication(res.application)
    setConsistency(res.consistency)
    setAccepted((prev) => {
      const next = new Set(prev)
      if (res.validation.status === 'accepted') next.add(slot)
      else next.delete(slot)
      return next
    })
  }

  async function submit() {
    if (!application) return
    rememberApplication(application.id)
    setSubmitted(true)
  }

  const allAccepted = slots.every((s) => accepted.has(s))
  const name = lang === 'ta' ? scheme.nameTa : scheme.nameEn

  if (submitted && application) {
    return (
      <div className="mx-auto max-w-lg space-y-5 text-center">
        <span className="mx-auto flex size-16 items-center justify-center rounded-full bg-success-soft text-success">
          <CheckCircle2 className="size-9" aria-hidden />
        </span>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t('v2.apply.submitted')}</h1>
          <p className="mt-1 text-muted-foreground">{t('v2.apply.submittedDesc', { id: application.id })}</p>
        </div>
        <div className="flex flex-col justify-center gap-2 sm:flex-row">
          <Button asChild size="lg">
            <Link to={`/portal/track/${application.id}`}>{t('v2.apply.viewTracking')}</Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link to="/portal/services">{t('v2.apply.backToServices')}</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <Breadcrumbs items={[{ label: t('v2.services.title'), to: '/portal/services' }, { label: name }]} />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('v2.apply.title', { service: name })}</h1>
        <p className="text-muted-foreground">{t('v2.apply.subtitle')}</p>
      </div>

      {!application ? (
        <Card className="mx-auto max-w-md">
          <CardHeader>
            <CardTitle className="text-base">{t('v2.apply.step1')}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={start} className="space-y-4">
              <div className="space-y-1.5">
                <Label>{t('v2.login.name')}</Label>
                <Input value={profile?.kind === 'citizen' ? profile.name : ''} disabled />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="apply-office">{t('v2.apply.centre')}</Label>
                <Select value={officeId} onValueChange={setOfficeId}>
                  <SelectTrigger id="apply-office" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {offices.map((o) => (
                      <SelectItem key={o.id} value={o.id}>
                        {o.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button type="submit" size="lg" disabled={busy || !officeId} className="w-full">
                {t('v2.apply.start')}
              </Button>
            </form>
          </CardContent>
        </Card>
      ) : (
        <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <section className="space-y-4" aria-label={t('v2.apply.step2')}>
            <p className="text-sm font-medium text-muted-foreground">{t('v2.apply.documentsNeeded')}</p>
            {slots.map((slot) => (
              <ApplySlot key={slot} slot={slot} applicationId={application.id} supportingType={supportingType} onUploaded={(res) => onUploaded(slot, res)} />
            ))}
          </section>
          <aside className="space-y-4 lg:sticky lg:top-24">
            {consistency && <ConsistencyCard consistency={consistency} />}
            <Card>
              <CardContent className="space-y-3">
                {allAccepted ? (
                  <p className="flex items-center gap-2 text-sm text-success">
                    <CircleCheck className="size-4 shrink-0" aria-hidden />
                    {t('v2.apply.allAccepted')}
                  </p>
                ) : (
                  <p className="flex items-center gap-2 text-sm text-muted-foreground">
                    <FileWarning className="size-4 shrink-0" aria-hidden />
                    {t('v2.apply.someRemaining', { n: slots.length - accepted.size, total: slots.length })}
                  </p>
                )}
                <Button size="lg" className="w-full" disabled={!allAccepted} onClick={submit}>
                  <Send aria-hidden />
                  {t('v2.apply.submit')}
                </Button>
                {application.status === 'ready_for_officer' && (
                  <p className="flex items-center gap-1 text-xs text-muted-foreground">
                    <ExternalLink className="size-3.5" aria-hidden />
                    {application.id}
                  </p>
                )}
              </CardContent>
            </Card>
          </aside>
        </div>
      )}
    </div>
  )
}
