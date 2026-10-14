import { Landmark, ShieldCheck, Sparkles } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import type { Stage } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useLang } from '@/i18n'
import { STAGE_ORDER, stageName } from '@/lib/services'
import { PortalFooter } from '@/v2/components/PortalFooter'
import { PrototypeBanner, TricolorRibbon } from '@/v2/components/PrototypeBanner'
import { useAuth } from '@/v2/auth'

/** Mock department sign-in. Accepts any input, plus a one-click demo account per role. */
export function DepartmentLoginPage() {
  const { t, lang } = useLang()
  const { loginDepartment } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [role, setRole] = useState<Stage>('vao')

  function enter(values: { name: string; role: Stage }) {
    loginDepartment(values)
    navigate('/department')
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    enter({ name: name.trim() || stageName(role, lang), role })
  }

  return (
    <div className="flex min-h-screen flex-col">
      <TricolorRibbon />
      <PrototypeBanner />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-10">
        <div className="mb-6 text-center">
          <span className="mx-auto flex size-14 items-center justify-center rounded-full" style={{ background: 'var(--primary)' }}>
            <Landmark className="size-7 text-white" aria-hidden />
          </span>
          <h1 className="mt-3 text-xl font-semibold">{t('v2.login.department')}</h1>
          <p className="text-sm text-muted-foreground">{t('v2.login.departmentSubtitle')}</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t('v2.login.title')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="dept-name">{t('v2.login.name')}</Label>
                <Input id="dept-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="S. Meena" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="dept-role">{t('v2.login.role')}</Label>
                <Select value={role} onValueChange={(v) => setRole(v as Stage)}>
                  <SelectTrigger id="dept-role" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STAGE_ORDER.map((s) => (
                      <SelectItem key={s} value={s}>
                        {stageName(s, lang)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button type="submit" size="lg" className="w-full">
                <ShieldCheck aria-hidden />
                {t('v2.login.submit')}
              </Button>
            </form>
            <Button type="button" variant="outline" size="lg" className="w-full" onClick={() => enter({ name: 'S. Meena', role: 'tahsildar' })}>
              <Sparkles aria-hidden />
              {t('v2.login.demo')}
            </Button>
            <p className="text-center text-xs text-muted-foreground">{t('v2.login.demoNotice')}</p>
          </CardContent>
        </Card>
        <Link to="/login" className="mt-4 block text-center text-sm text-primary hover:underline">
          {t('v2.login.switch', { kind: t('v2.login.citizen') })}
        </Link>
      </main>
      <PortalFooter />
    </div>
  )
}
