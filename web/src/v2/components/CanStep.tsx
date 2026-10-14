// CAN step (contract v1.5), shared by the citizen Apply flow and the operator's counter Apply flow. A CAN is created
// once per mobile number and never edited; its name/DOB are what the certificate prints, so after this step they
// are shown locked and the application is created from the CAN instead of retyped text.
import { BadgeCheck, IdCard, Lock, TriangleAlert } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import { toast } from 'sonner'

import { createOrFindCitizen, getCitizen } from '@/api/client'
import type { Citizen } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useLang } from '@/i18n'
import { isoDateToDisplay } from '@/lib/format'

const MOBILE = /^[6-9]\d{9}$/
const PIN = /^[1-9]\d{5}$/

function normaliseName(name: string): string {
  return name.trim().replace(/\s+/g, ' ').toUpperCase()
}

export function CanStep({
  mode,
  defaults,
  knownCan,
  citizen,
  onChange,
}: {
  /** citizen: phone is the signed-in number and can't be changed. operator: looking up a citizen at the counter. */
  mode: 'citizen' | 'operator'
  defaults: { name: string; phone: string; dob: string | null }
  /** A CAN this browser already knows for the signed-in citizen: shown straight away, no form. */
  knownCan?: string | null
  citizen: Citizen | null
  onChange: (citizen: Citizen | null) => void
}) {
  const { t } = useLang()
  const [name, setName] = useState(defaults.name)
  const [phone, setPhone] = useState(defaults.phone)
  const [dob, setDob] = useState(defaults.dob ?? '')
  const [address, setAddress] = useState('')
  const [pin, setPin] = useState('')
  const [busy, setBusy] = useState(false)
  const [loadingKnown, setLoadingKnown] = useState(Boolean(knownCan) && !citizen)
  const [phoneError, setPhoneError] = useState(false)
  const [outcome, setOutcome] = useState<{ created: boolean; typedName: string } | null>(null)

  useEffect(() => {
    if (!knownCan || citizen) return
    let cancelled = false
    getCitizen(knownCan)
      .then((c) => !cancelled && onChange(c))
      .catch(() => {}) // unknown/stale CAN: fall back to the form
      .finally(() => !cancelled && setLoadingKnown(false))
    return () => {
      cancelled = true
    }
  }, [knownCan, citizen, onChange])

  const digits = phone.replace(/\D/g, '').slice(-10)
  const pinInvalid = pin !== '' && !PIN.test(pin)

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!MOBILE.test(digits)) {
      setPhoneError(true)
      return
    }
    if (pinInvalid) return
    setBusy(true)
    try {
      const { citizen: c, created } = await createOrFindCitizen({
        name: name.trim(),
        phone: digits,
        dob: dob || null,
        address_line: address.trim() || null,
        pin_code: pin || null,
      })
      setOutcome({ created, typedName: normaliseName(name) })
      onChange(c)
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setBusy(false)
    }
  }

  function reset() {
    setOutcome(null)
    setPhone('')
    setName('')
    setDob('')
    setAddress('')
    setPin('')
    onChange(null)
  }

  if (loadingKnown) {
    return (
      <Card className="mx-auto w-full max-w-md">
        <CardContent className="py-8 text-center text-sm text-muted-foreground">{t('v2.can.loading')}</CardContent>
      </Card>
    )
  }

  if (citizen) {
    const nameIgnored = outcome !== null && !outcome.created && outcome.typedName !== citizen.name
    return (
      <Card className="mx-auto w-full max-w-md border-primary/30" data-testid="can-card">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <IdCard className="size-5 text-primary" aria-hidden />
            {t('v2.can.title')}
          </CardTitle>
          {outcome && (
            <Badge className={outcome.created ? 'bg-success-soft text-success' : 'bg-accent text-primary'}>
              <BadgeCheck aria-hidden />
              {t(outcome.created ? 'v2.can.created' : 'v2.can.found')}
            </Badge>
          )}
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="font-mono text-2xl font-semibold tracking-wider">{citizen.can}</p>
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
            <dt className="text-muted-foreground">{t('field.name')}</dt>
            <dd className="flex items-center gap-1.5 font-medium">
              {citizen.name}
              <Lock className="size-3.5 text-muted-foreground" aria-label={t('v2.can.lockedShort')} />
            </dd>
            <dt className="text-muted-foreground">{t('field.dob')}</dt>
            <dd className="flex items-center gap-1.5 font-medium">
              {citizen.dob ? isoDateToDisplay(citizen.dob) : '—'}
              <Lock className="size-3.5 text-muted-foreground" aria-label={t('v2.can.lockedShort')} />
            </dd>
            <dt className="text-muted-foreground">{t('v2.login.phone')}</dt>
            <dd className="font-mono">{citizen.phone_masked}</dd>
            {(citizen.address_line || citizen.pin_code) && (
              <>
                <dt className="text-muted-foreground">{t('v2.can.addressLabel')}</dt>
                <dd>{[citizen.address_line, citizen.pin_code].filter(Boolean).join(' – ')}</dd>
              </>
            )}
          </dl>
          {nameIgnored && (
            <p className="flex gap-2 rounded-md bg-warning-soft px-2.5 py-2 text-sm text-warning">
              <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              {t('v2.can.nameIgnored')}
            </p>
          )}
          <p className="flex gap-2 rounded-md bg-muted px-2.5 py-2 text-xs text-muted-foreground">
            <Lock className="mt-0.5 size-3.5 shrink-0" aria-hidden />
            {t('v2.can.locked')}
          </p>
          {mode === 'operator' && (
            <Button type="button" variant="outline" size="sm" onClick={reset}>
              {t('v2.can.useDifferent')}
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="mx-auto w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <IdCard className="size-5 text-primary" aria-hidden />
          {t('v2.can.title')}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{t(mode === 'operator' ? 'v2.can.introOperator' : 'v2.can.intro')}</p>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="can-phone">{t('v2.login.phone')}</Label>
            <Input
              id="can-phone"
              required
              inputMode="tel"
              value={phone}
              readOnly={mode === 'citizen'}
              onChange={(e) => {
                setPhone(e.target.value)
                setPhoneError(false)
              }}
              placeholder="98765 43221"
              aria-invalid={phoneError}
              aria-describedby="can-phone-help"
            />
            <p id="can-phone-help" className={phoneError ? 'text-xs text-danger' : 'text-xs text-muted-foreground'}>
              {phoneError ? t('v2.login.phoneInvalid') : t(mode === 'citizen' ? 'v2.can.phoneFromLogin' : 'v2.can.phoneHint')}
            </p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="can-name">{t('v2.can.nameAsOnAadhaar')}</Label>
            <Input id="can-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="R. Karthik" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="can-dob">{t('v2.login.dob')}</Label>
            <Input id="can-dob" type="date" value={dob} max={new Date().toISOString().slice(0, 10)} onChange={(e) => setDob(e.target.value)} />
          </div>
          <div className="grid gap-4 sm:grid-cols-[1fr_8rem]">
            <div className="space-y-1.5">
              <Label htmlFor="can-address">{t('v2.can.address')}</Label>
              <Input id="can-address" value={address} maxLength={200} onChange={(e) => setAddress(e.target.value)} placeholder="27, Gandhi Street, Sulur" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="can-pin">{t('v2.can.pin')}</Label>
              <Input
                id="can-pin"
                inputMode="numeric"
                value={pin}
                onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="641402"
                aria-invalid={pinInvalid}
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">{t('v2.can.createNote')}</p>
          <Button type="submit" size="lg" className="w-full" disabled={busy || name.trim() === '' || pinInvalid}>
            <IdCard aria-hidden />
            {t('v2.can.submit')}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
