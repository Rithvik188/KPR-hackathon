import { BadgeCheck, Landmark, ShieldCheck } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import type { Stage } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useLang } from '@/i18n'
import { stageName } from '@/lib/services'
import { roleFromStaffId, useAuth } from '@/v2/auth'
import { LoginShell } from '@/v2/components/LoginShell'
import { MockCaptcha } from '@/v2/components/MockCaptcha'

// One demo officer per stage, so the VAO → RI → Tahsildar chain can be walked live by signing in as each.
const DEMO_OFFICERS: { role: Stage; name: string; staffId: string }[] = [
  { role: 'vao', name: 'S. Meena', staffId: 'VAO-SULUR-014' },
  { role: 'ri', name: 'K. Arun', staffId: 'RI-SULUR-007' },
  { role: 'tahsildar', name: 'R. Lakshmi', staffId: 'TAH-SULUR-001' },
]

/** Mock department sign-in. The staff ID's prefix (VAO / RI / TAH) is the only source of the role, so a VAO
 * can't sign in as RI or Tahsildar by picking a different option: there is no option to pick. */
export function DepartmentLoginPage() {
  const { t, lang } = useLang()
  const { loginDepartment } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [staffId, setStaffId] = useState('')
  const [captchaSolved, setCaptchaSolved] = useState(false)

  const role = roleFromStaffId(staffId)
  const canSubmit = name.trim() !== '' && role !== null && captchaSolved

  function submit(e: FormEvent) {
    e.preventDefault()
    if (canSubmit && loginDepartment({ name: name.trim(), employeeId: staffId })) navigate('/department')
  }

  return (
    <LoginShell current="department" icon={Landmark} title={t('v2.login.department')} subtitle={t('v2.login.departmentSubtitle')}>
      <form onSubmit={submit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="dept-name">{t('v2.login.name')}</Label>
          <Input id="dept-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="S. Meena" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="dept-staff-id">{t('v2.login.staffId')}</Label>
          <Input
            id="dept-staff-id"
            required
            autoComplete="off"
            spellCheck={false}
            className="font-mono uppercase"
            value={staffId}
            onChange={(e) => setStaffId(e.target.value.toUpperCase().replace(/\s/g, ''))}
            placeholder="VAO-SULUR-014"
            aria-invalid={staffId !== '' && role === null}
            aria-describedby="dept-staff-id-help"
          />
          <div id="dept-staff-id-help" aria-live="polite">
            {role ? (
              <p className="flex items-center gap-1.5 rounded-md bg-success-soft px-2.5 py-1.5 text-sm font-medium text-success">
                <BadgeCheck className="size-4 shrink-0" aria-hidden />
                {t('v2.login.signingInAs', { role: stageName(role, lang) })}
              </p>
            ) : staffId.length >= 10 ? ( // the shortest valid ID (RI-ABC-123) is 10 characters: don't nag earlier
              <p className="text-xs text-danger">{t('v2.login.staffIdInvalid')}</p>
            ) : (
              <p className="text-xs text-muted-foreground">{t('v2.login.staffIdHint')}</p>
            )}
          </div>
        </div>
        <MockCaptcha onSolvedChange={setCaptchaSolved} />
        <Button type="submit" size="lg" className="w-full" disabled={!canSubmit}>
          <ShieldCheck aria-hidden />
          {role ? `${t('v2.login.submit')} · ${stageName(role, lang)}` : t('v2.login.submit')}
        </Button>
      </form>
      <div className="space-y-2 rounded-lg border border-dashed p-3">
        <p className="text-xs font-medium text-muted-foreground">{t('v2.login.demoIds')}</p>
        <div className="flex flex-wrap gap-2">
          {DEMO_OFFICERS.map((d) => (
            <Button
              key={d.staffId}
              type="button"
              size="sm"
              variant="outline"
              className="font-mono"
              onClick={() => {
                setName(d.name)
                setStaffId(d.staffId)
              }}
            >
              {d.staffId}
            </Button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">{t('v2.login.demoIdsNote')}</p>
      </div>
    </LoginShell>
  )
}
