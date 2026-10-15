import { LoaderCircle, MessageSquareText, ShieldCheck, Sparkles, UserRound } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { requestOtp } from '@/api/client'
import type { OtpSent } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { type I18nKey, useLang } from '@/i18n'
import { signInErrorKey, useAuth } from '@/v2/auth'
import { LoginShell } from '@/v2/components/LoginShell'

const MOBILE = /^[6-9]\d{9}$/
const DEMO_CITIZEN = { name: 'R. Karthik', phone: '9876543221', dob: '1998-04-12' }

/** Citizen sign-in with an OTP checked by the server (contract v1.8). The prototype has no SMS gateway, so the
 * server returns the code and this page shows it, labelled as a demo. The demo button goes through the same two
 * calls with a demo number. */
export function CitizenLoginPage() {
  const { t } = useLang()
  const { signInCitizen } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [dob, setDob] = useState('')
  const [phoneError, setPhoneError] = useState(false)
  const [sent, setSent] = useState<OtpSent | null>(null) // null until Send OTP succeeds
  const [otp, setOtp] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<I18nKey | null>(null)

  const digits = phone.replace(/\D/g, '').slice(-10)

  async function sendOtp(to = digits): Promise<OtpSent | null> {
    if (!MOBILE.test(to)) {
      setPhoneError(true)
      return null
    }
    setPhoneError(false)
    setError(null)
    setBusy(true)
    try {
      const res = await requestOtp(to)
      setSent(res)
      setOtp('')
      return res
    } catch (err) {
      setError(signInErrorKey(err))
      return null
    } finally {
      setBusy(false)
    }
  }

  async function verify(citizen: { name: string; phone: string; dob: string | null }, code: string) {
    setError(null)
    setBusy(true)
    try {
      await signInCitizen(citizen, code)
      navigate('/portal')
    } catch (err) {
      setError(signInErrorKey(err))
      setBusy(false)
    }
  }

  function changePhone() {
    setSent(null)
    setOtp('')
    setError(null)
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    if (busy) return
    if (sent === null) void sendOtp()
    else if (otp.length === 6) void verify({ name: name.trim(), phone: digits, dob: dob || null }, otp)
  }

  async function signInDemo() {
    setName(DEMO_CITIZEN.name)
    setPhone(DEMO_CITIZEN.phone)
    setDob(DEMO_CITIZEN.dob)
    const res = await sendOtp(DEMO_CITIZEN.phone)
    // With no demo code (a real SMS setup) the OTP step stays open for the code to be typed in.
    if (res?.demo_otp) await verify(DEMO_CITIZEN, res.demo_otp)
  }

  return (
    <LoginShell current="citizen" icon={UserRound} title={t('v2.login.citizen')} subtitle={t('v2.login.citizenSubtitle')}>
      <form onSubmit={submit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="login-name">{t('v2.login.name')}</Label>
          <Input id="login-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="R. Karthik" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="login-phone">{t('v2.login.phone')}</Label>
          <Input
            id="login-phone"
            required
            inputMode="tel"
            autoComplete="tel"
            value={phone}
            readOnly={sent !== null}
            onChange={(e) => {
              setPhone(e.target.value)
              setPhoneError(false)
            }}
            placeholder="98765 43221"
            aria-invalid={phoneError}
            aria-describedby={phoneError ? 'login-phone-error' : undefined}
          />
          {phoneError && (
            <p id="login-phone-error" className="text-xs text-danger">
              {t('v2.login.phoneInvalid')}
            </p>
          )}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="login-dob">{t('v2.login.dob')}</Label>
          <Input id="login-dob" type="date" value={dob} max={new Date().toISOString().slice(0, 10)} onChange={(e) => setDob(e.target.value)} />
        </div>

        {sent === null ? (
          <Button type="submit" size="lg" className="w-full" disabled={busy || name.trim() === '' || phone.trim() === ''}>
            {busy ? <LoaderCircle className="animate-spin" aria-hidden /> : <MessageSquareText aria-hidden />}
            {t('v2.login.sendOtp')}
          </Button>
        ) : (
          <>
            <div className="rounded-md border border-dashed bg-accent/60 px-3 py-2 text-sm" role="status">
              {sent.demo_otp
                ? t('v2.login.otpDemo', { code: sent.demo_otp, to: sent.sent_to })
                : t('v2.login.otpSent', { to: sent.sent_to })}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="login-otp">{t('v2.login.otp')}</Label>
              <Input
                id="login-otp"
                inputMode="numeric"
                autoComplete="one-time-code"
                className="font-mono tracking-[0.4em]"
                value={otp}
                onChange={(e) => {
                  setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))
                  setError(null)
                }}
                aria-invalid={error === 'v2.login.otpWrong'}
                autoFocus
              />
              <div className="flex gap-3 text-xs">
                <button type="button" className="text-primary hover:underline" onClick={() => void sendOtp()} disabled={busy}>
                  {t('v2.login.otpResend')}
                </button>
                <button type="button" className="text-primary hover:underline" onClick={changePhone} disabled={busy}>
                  {t('v2.login.changePhone')}
                </button>
              </div>
            </div>
            <Button type="submit" size="lg" className="w-full" disabled={busy || otp.length !== 6 || name.trim() === ''}>
              {busy ? <LoaderCircle className="animate-spin" aria-hidden /> : <ShieldCheck aria-hidden />}
              {busy ? t('v2.login.signingIn') : t('v2.login.submit')}
            </Button>
          </>
        )}
        {error && (
          <p role="alert" className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">
            {t(error)}
          </p>
        )}
      </form>
      <Button type="button" variant="outline" size="lg" className="w-full" disabled={busy} onClick={() => void signInDemo()}>
        <Sparkles aria-hidden />
        {t('v2.login.demo')}
      </Button>
    </LoginShell>
  )
}
