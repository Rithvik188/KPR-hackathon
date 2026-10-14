import { ShieldCheck, Sparkles, UserRound } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useLang } from '@/i18n'
import { PortalFooter } from '@/v2/components/PortalFooter'
import { PrototypeBanner, TricolorRibbon } from '@/v2/components/PrototypeBanner'
import { useAuth } from '@/v2/auth'

/** Mock citizen sign-in. Accepts any input, plus a one-click demo account — no real credentials are ever collected. */
export function CitizenLoginPage() {
  const { t } = useLang()
  const { loginCitizen } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [dob, setDob] = useState('')

  function enter(values: { name: string; phone: string; dob: string | null }) {
    loginCitizen(values)
    navigate('/portal')
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    enter({ name: name.trim() || 'Citizen', phone: phone.trim() || '9876543210', dob: dob || null })
  }

  return (
    <div className="flex min-h-screen flex-col">
      <TricolorRibbon />
      <PrototypeBanner />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-10">
        <div className="mb-6 text-center">
          <span className="mx-auto flex size-14 items-center justify-center rounded-full" style={{ background: 'var(--primary)' }}>
            <UserRound className="size-7 text-white" aria-hidden />
          </span>
          <h1 className="mt-3 text-xl font-semibold">{t('v2.login.citizen')}</h1>
          <p className="text-sm text-muted-foreground">{t('v2.login.citizenSubtitle')}</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t('v2.login.title')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="login-name">{t('v2.login.name')}</Label>
                <Input id="login-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="R. Karthik" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="login-phone">{t('v2.login.phone')}</Label>
                <Input id="login-phone" required inputMode="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="98765 43221" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="login-dob">{t('v2.login.dob')}</Label>
                <Input id="login-dob" type="date" value={dob} max={new Date().toISOString().slice(0, 10)} onChange={(e) => setDob(e.target.value)} />
              </div>
              <Button type="submit" size="lg" className="w-full">
                <ShieldCheck aria-hidden />
                {t('v2.login.submit')}
              </Button>
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
            <p className="text-center text-xs text-muted-foreground">{t('v2.login.demoNotice')}</p>
          </CardContent>
        </Card>
        <Link to="/department-login" className="mt-4 block text-center text-sm text-primary hover:underline">
          {t('v2.login.switch', { kind: t('v2.login.department') })}
        </Link>
      </main>
      <PortalFooter />
    </div>
  )
}
