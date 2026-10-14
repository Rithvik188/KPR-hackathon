import { Plus, UserRound } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import { toast } from 'sonner'

import { createApplication, getOffices } from '@/api/client'
import type { ApplicationSummary, Office, Service } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useLang } from '@/i18n'

const SERVICES: Service[] = ['community_certificate', 'income_certificate', 'nativity_certificate', 'ration_card_update']
const OFFICE_KEY = 'sevaicheck.office'

function readOffice(): string {
  try {
    return localStorage.getItem(OFFICE_KEY) ?? ''
  } catch {
    return ''
  }
}

function saveOffice(id: string) {
  try {
    localStorage.setItem(OFFICE_KEY, id)
  } catch {
    // storage unavailable: the choice lasts for this page only
  }
}

/** Step 1: the operator's centre plus the citizen's details, then Create. Collapses once created. */
export function OperatorBar({
  application,
  onCreated,
  onReset,
}: {
  application: ApplicationSummary | null
  onCreated: (app: ApplicationSummary) => void
  onReset: () => void
}) {
  const { t } = useLang()
  const [offices, setOffices] = useState<Office[]>([])
  const [officeId, setOfficeId] = useState(readOffice)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [service, setService] = useState<Service>('community_certificate')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getOffices()
      .then((list) => {
        setOffices(list)
        setOfficeId((current) => (list.some((o) => o.id === current) ? current : (list[0]?.id ?? '')))
      })
      .catch((err) => toast.error(t('common.error'), { description: String(err.message ?? err) }))
  }, [t])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      onCreated(await createApplication({ citizen_name: name, phone, service, office_id: officeId }))
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setBusy(false)
    }
  }

  if (application) {
    return (
      <Card className="py-4">
        <CardContent className="flex-row flex-wrap items-center gap-x-6 gap-y-2">
          <div className="flex items-center gap-2">
            <UserRound className="size-5 text-primary" aria-hidden />
            <span className="font-semibold">{application.citizen_name}</span>
          </div>
          <span className="text-sm text-muted-foreground tabular-nums">{application.phone_masked}</span>
          <span className="text-sm text-muted-foreground">{t(`service.${application.service}`)}</span>
          <span className="text-sm text-muted-foreground">{application.office_name}</span>
          <Button variant="outline" size="sm" className="ml-auto" onClick={onReset}>
            <Plus aria-hidden />
            {t('counter.newApplication')}
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent>
        <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="space-y-1.5">
            <Label htmlFor="office">{t('counter.office')}</Label>
            <Select
              value={officeId}
              onValueChange={(v) => {
                setOfficeId(v)
                saveOffice(v)
              }}
            >
              <SelectTrigger id="office" className="w-full">
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
          <div className="space-y-1.5">
            <Label htmlFor="citizen-name">{t('counter.citizenName')}</Label>
            <Input id="citizen-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="R. Karthik" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="phone">{t('counter.phone')}</Label>
            <Input
              id="phone"
              required
              inputMode="tel"
              pattern="[+0-9 ]{10,16}"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="98765 43221"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="service">{t('counter.service')}</Label>
            <Select value={service} onValueChange={(v) => setService(v as Service)}>
              <SelectTrigger id="service" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SERVICES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {t(`service.${s}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="sm:col-span-2 xl:col-span-4">
            <Button type="submit" size="lg" disabled={busy || !officeId}>
              {t('counter.create')}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
