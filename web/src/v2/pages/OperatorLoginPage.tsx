import { BadgeCheck, ShieldCheck, Store } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { getOffices } from '@/api/client'
import type { Office } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useLang } from '@/i18n'
import { centreTypeOf, type CentreType, useAuth } from '@/v2/auth'
import { LoginShell } from '@/v2/components/LoginShell'
import { MockCaptcha } from '@/v2/components/MockCaptcha'

const MIN_ID = 4

// Demo operators. The office is picked from the live list by centre type, so the buttons work against the real
// backend and in fixture mode alike. Sulur 2 is preferred for govt because the seeded data raises notices there.
const DEMO_OPERATORS: { type: CentreType; name: string; staffId: string; prefer?: string }[] = [
  { type: 'govt', name: 'P. Divya', staffId: 'ESV-SULUR2-031', prefer: 'off_sulur_es2' },
  { type: 'private', name: 'M. Farooq', staffId: 'ESV-PVT-112' },
]

/** Mock sign-in for govt-run and private e-Sevai centre operators. The centre type is never chosen: it is
 * whatever the selected office is. */
export function OperatorLoginPage() {
  const { t } = useLang()
  const { loginOperator } = useAuth()
  const navigate = useNavigate()
  const [offices, setOffices] = useState<Office[]>([])
  const [name, setName] = useState('')
  const [staffId, setStaffId] = useState('')
  const [officeId, setOfficeId] = useState('')
  const [captchaSolved, setCaptchaSolved] = useState(false)

  useEffect(() => {
    getOffices()
      .then((all) => setOffices(all.filter((o) => centreTypeOf(o) !== null)))
      .catch(() => setOffices([]))
  }, [])

  const office = offices.find((o) => o.id === officeId)
  const centreType = office ? centreTypeOf(office) : null
  const canSubmit = name.trim() !== '' && staffId.trim().length >= MIN_ID && office !== undefined && captchaSolved

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!canSubmit || !office) return
    if (loginOperator({ name: name.trim(), employeeId: staffId, office })) navigate('/operator')
  }

  function fillDemo(demo: (typeof DEMO_OPERATORS)[number]) {
    const ofType = offices.filter((o) => centreTypeOf(o) === demo.type)
    const pick = ofType.find((o) => o.id === demo.prefer) ?? ofType[0]
    setName(demo.name)
    setStaffId(demo.staffId)
    if (pick) setOfficeId(pick.id)
  }

  return (
    <LoginShell current="operator" icon={Store} title={t('v2.login.operator')} subtitle={t('v2.login.operatorSubtitle')}>
      <form onSubmit={submit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="op-name">{t('v2.login.name')}</Label>
          <Input id="op-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="P. Divya" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="op-staff-id">{t('v2.login.operatorId')}</Label>
          <Input
            id="op-staff-id"
            required
            autoComplete="off"
            spellCheck={false}
            className="font-mono uppercase"
            value={staffId}
            onChange={(e) => setStaffId(e.target.value.toUpperCase().replace(/\s/g, ''))}
            placeholder="ESV-SULUR2-031"
            aria-describedby="op-staff-id-help"
          />
          <p id="op-staff-id-help" className="text-xs text-muted-foreground">
            {t('v2.login.operatorIdHint')}
          </p>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="op-centre">{t('v2.login.centre')}</Label>
          <Select value={officeId} onValueChange={setOfficeId}>
            <SelectTrigger id="op-centre" className="w-full">
              <SelectValue placeholder={t('v2.login.centrePlaceholder')} />
            </SelectTrigger>
            <SelectContent>
              {offices.map((o) => (
                <SelectItem key={o.id} value={o.id}>
                  {o.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {centreType && (
            <p className="flex items-center gap-1.5 rounded-md bg-success-soft px-2.5 py-1.5 text-sm font-medium text-success" aria-live="polite">
              <BadgeCheck className="size-4 shrink-0" aria-hidden />
              {t(centreType === 'govt' ? 'v2.login.centreGovt' : 'v2.login.centrePrivate')}
            </p>
          )}
        </div>
        <MockCaptcha onSolvedChange={setCaptchaSolved} />
        <Button type="submit" size="lg" className="w-full" disabled={!canSubmit}>
          <ShieldCheck aria-hidden />
          {t('v2.login.submit')}
        </Button>
      </form>
      <div className="space-y-2 rounded-lg border border-dashed p-3">
        <p className="text-xs font-medium text-muted-foreground">{t('v2.login.demoIds')}</p>
        <div className="flex flex-wrap gap-2">
          {DEMO_OPERATORS.map((d) => (
            <Button key={d.staffId} type="button" size="sm" variant="outline" onClick={() => fillDemo(d)} disabled={offices.length === 0}>
              {t(d.type === 'govt' ? 'v2.login.demoGovt' : 'v2.login.demoPrivate')}
            </Button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">{t('v2.login.demoIdsNote')}</p>
      </div>
    </LoginShell>
  )
}
