import { MessageSquareText, ShieldCheck, Sparkles, UserRound } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useLang } from '@/i18n'
import { useAuth } from '@/v2/auth'
import { LoginShell } from '@/v2/components/LoginShell'

const MOBILE = /^[6-9]\d{9}$/

function newOtp(): string {
  return String(100000 + Math.floor(Math.random() * 900000))
}

/** Mock citizen sign-in with a mock OTP step. The "OTP" is generated and shown right here in the page: no SMS is
 * sent and no real credentials are collected. The demo button skips the whole thing for the live demo. */
export function CitizenLoginPage() {
  const { t } = useLang()
  const { loginCitizen } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [dob, setDob] = useState('')
  const [phoneError, setPhoneError] = useState(false)
  const [otp, setOtp] = useState<string | null>(null) // the code "sent"; null until Send OTP
  const [otpInput, setOtpInput] = useState('')

  const digits = phone.replace(/\D/g, '').slice(-10)
  const otpOk = otp !== null && otpInput === otp

  function enter(values: { name: string; phone: string; dob: string | null }) {
    loginCitizen(values)
    navigate('/portal')
  }

  function sendOtp() {
    if (!MOBILE.test(digits)) {
      setPhoneError(true)
      return
    }
    setPhoneError(false)
    setOtp(newOtp())
    setOtpInput('')
  }

  function changePhone() {
    setOtp(null)
    setOtpInput('')
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    if (otp === null) sendOtp()
    else if (otpOk) enter({ name: name.trim(), phone: digits, dob: dob || null })
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
            readOnly={otp !== null}
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

        {otp === null ? (
          <Button type="submit" size="lg" className="w-full" disabled={name.trim() === '' || phone.trim() === ''}>
            <MessageSquareText aria-hidden />
            {t('v2.login.sendOtp')}
          </Button>
        ) : (
          <>
            <div className="rounded-md border border-dashed bg-accent/60 px-3 py-2 text-sm" role="status">
              {t('v2.login.otpDemo', { code: otp })}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="login-otp">{t('v2.login.otp')}</Label>
              <Input
                id="login-otp"
                inputMode="numeric"
                autoComplete="one-time-code"
                className="font-mono tracking-[0.4em]"
                value={otpInput}
                onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, '').slice(0, 6))}
                aria-invalid={otpInput.length === 6 && !otpOk}
                aria-describedby={otpInput.length === 6 && !otpOk ? 'login-otp-error' : undefined}
                autoFocus
              />
              {otpInput.length === 6 && !otpOk && (
                <p id="login-otp-error" className="text-xs text-danger">
                  {t('v2.login.otpWrong')}
                </p>
              )}
              <div className="flex gap-3 text-xs">
                <button type="button" className="text-primary hover:underline" onClick={sendOtp}>
                  {t('v2.login.otpResend')}
                </button>
                <button type="button" className="text-primary hover:underline" onClick={changePhone}>
                  {t('v2.login.changePhone')}
                </button>
              </div>
            </div>
            <Button type="submit" size="lg" className="w-full" disabled={!otpOk}>
              <ShieldCheck aria-hidden />
              {t('v2.login.submit')}
            </Button>
          </>
        )}
      </form>
      <Button
        type="button"
        variant="outline"
        size="lg"
        className="w-full"
        onClick={() => enter({ name: 'R. Karthik', phone: '9876543221', dob: '1998-04-12' })}
      >
        <Sparkles aria-hidden />
        {t('v2.login.demo')}
      </Button>
    </LoginShell>
  )
}
