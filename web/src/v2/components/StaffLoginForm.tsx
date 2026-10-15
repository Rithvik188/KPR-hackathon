import { LoaderCircle, ShieldCheck } from 'lucide-react'
import { type FormEvent, type ReactNode, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { type I18nKey, useLang } from '@/i18n'
import { signInErrorKey } from '@/v2/auth'
import { MockCaptcha } from '@/v2/components/MockCaptcha'

/** Staff ID + password sign-in, shared by the department and operator logins. The server checks the password and
 * decides the role and centre; the demo buttons fill in only the ID, never the password. */
export function StaffLoginForm({
  idPrefix,
  idLabel,
  idPlaceholder,
  idHelp,
  canSubmitId,
  submitLabel,
  demos,
  signIn,
  onSignedIn,
}: {
  idPrefix: string
  idLabel: string
  idPlaceholder: string
  idHelp: (staffId: string) => ReactNode
  canSubmitId: (staffId: string) => boolean
  submitLabel: (staffId: string) => string
  demos: { label: string; staffId: string }[]
  signIn: (staffId: string, password: string) => Promise<void>
  onSignedIn: () => void
}) {
  const { t } = useLang()
  const [staffId, setStaffId] = useState('')
  const [password, setPassword] = useState('')
  const [captchaSolved, setCaptchaSolved] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<I18nKey | null>(null)

  const canSubmit = canSubmitId(staffId) && password !== '' && captchaSolved && !busy

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    setBusy(true)
    setError(null)
    try {
      await signIn(staffId, password)
      onSignedIn()
    } catch (err) {
      setError(signInErrorKey(err))
      setPassword('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <form onSubmit={submit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor={`${idPrefix}-staff-id`}>{idLabel}</Label>
          <Input
            id={`${idPrefix}-staff-id`}
            required
            autoComplete="username"
            spellCheck={false}
            className="font-mono uppercase"
            value={staffId}
            onChange={(e) => {
              setStaffId(e.target.value.toUpperCase().replace(/\s/g, ''))
              setError(null)
            }}
            placeholder={idPlaceholder}
            aria-describedby={`${idPrefix}-staff-id-help`}
          />
          <div id={`${idPrefix}-staff-id-help`} aria-live="polite">
            {idHelp(staffId)}
          </div>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor={`${idPrefix}-password`}>{t('v2.login.password')}</Label>
          <Input
            id={`${idPrefix}-password`}
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value)
              setError(null)
            }}
            aria-invalid={error === 'v2.login.badCredentials'}
            aria-describedby={error ? `${idPrefix}-error` : undefined}
          />
        </div>
        <MockCaptcha onSolvedChange={setCaptchaSolved} />
        {error && (
          <p id={`${idPrefix}-error`} role="alert" className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">
            {t(error)}
          </p>
        )}
        <Button type="submit" size="lg" className="w-full" disabled={!canSubmit}>
          {busy ? <LoaderCircle className="animate-spin" aria-hidden /> : <ShieldCheck aria-hidden />}
          {busy ? t('v2.login.signingIn') : submitLabel(staffId)}
        </Button>
      </form>
      <div className="space-y-2 rounded-lg border border-dashed p-3">
        <p className="text-xs font-medium text-muted-foreground">{t('v2.login.demoIds')}</p>
        <div className="flex flex-wrap gap-2">
          {demos.map((d) => (
            <Button
              key={d.staffId}
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                setStaffId(d.staffId)
                setError(null)
              }}
            >
              {d.label}
            </Button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">{t('v2.login.demoIdsNote')}</p>
      </div>
    </>
  )
}
