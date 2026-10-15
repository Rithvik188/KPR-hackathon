import { Store } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { useLang } from '@/i18n'
import { useAuth } from '@/v2/auth'
import { LoginShell } from '@/v2/components/LoginShell'
import { StaffLoginForm } from '@/v2/components/StaffLoginForm'

const MIN_ID = 4

// Demo operators: one at a government-run centre (Sulur 2, where the seeded data raises notices) and one at a
// private franchise. Their centres are on their server accounts.
const DEMO_OPERATORS = [
  { label: 'v2.login.demoGovt', staffId: 'ESV-SULUR2-031' },
  { label: 'v2.login.demoPrivate', staffId: 'ESV-PVT-112' },
] as const

/** Sign-in for operators at government-run and private e-Sevai centres (contract v1.8). The centre, and with it
 * govt vs private, comes from the operator's account on the server: there is nothing to choose here. */
export function OperatorLoginPage() {
  const { t } = useLang()
  const { signInOperator } = useAuth()
  const navigate = useNavigate()

  return (
    <LoginShell current="operator" icon={Store} title={t('v2.login.operator')} subtitle={t('v2.login.operatorSubtitle')}>
      <StaffLoginForm
        idPrefix="op"
        idLabel={t('v2.login.operatorId')}
        idPlaceholder="ESV-SULUR2-031"
        idHelp={() => <p className="text-xs text-muted-foreground">{t('v2.login.operatorIdHint')}</p>}
        canSubmitId={(staffId) => staffId.trim().length >= MIN_ID}
        submitLabel={() => t('v2.login.submit')}
        demos={DEMO_OPERATORS.map((d) => ({ label: t(d.label), staffId: d.staffId }))}
        signIn={signInOperator}
        onSignedIn={() => navigate('/operator')}
      />
    </LoginShell>
  )
}
