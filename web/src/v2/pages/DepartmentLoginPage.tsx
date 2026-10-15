import { BadgeCheck, Landmark } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { useLang } from '@/i18n'
import { stageName } from '@/lib/services'
import { roleFromStaffId, useAuth } from '@/v2/auth'
import { LoginShell } from '@/v2/components/LoginShell'
import { StaffLoginForm } from '@/v2/components/StaffLoginForm'

// One demo officer per stage, so the VAO → RI → Tahsildar chain can be walked live by signing in as each.
const DEMO_STAFF_IDS = ['VAO-SULUR-014', 'RI-SULUR-007', 'TAH-SULUR-001']

/** Department sign-in (contract v1.8): staff ID + password, checked by the server, which also returns the role.
 * The ID's prefix is only a hint on this page; there is no role to pick. */
export function DepartmentLoginPage() {
  const { t, lang } = useLang()
  const { signInDepartment } = useAuth()
  const navigate = useNavigate()

  return (
    <LoginShell current="department" icon={Landmark} title={t('v2.login.department')} subtitle={t('v2.login.departmentSubtitle')}>
      <StaffLoginForm
        idPrefix="dept"
        idLabel={t('v2.login.staffId')}
        idPlaceholder="VAO-SULUR-014"
        idHelp={(staffId) => {
          const role = roleFromStaffId(staffId)
          if (role) {
            return (
              <p className="flex items-center gap-1.5 rounded-md bg-success-soft px-2.5 py-1.5 text-sm font-medium text-success">
                <BadgeCheck className="size-4 shrink-0" aria-hidden />
                {t('v2.login.signingInAs', { role: stageName(role, lang) })}
              </p>
            )
          }
          // the shortest valid ID (RI-ABC-123) is 10 characters: don't nag earlier
          return staffId.length >= 10 ? (
            <p className="text-xs text-danger">{t('v2.login.staffIdInvalid')}</p>
          ) : (
            <p className="text-xs text-muted-foreground">{t('v2.login.staffIdHint')}</p>
          )
        }}
        canSubmitId={(staffId) => roleFromStaffId(staffId) !== null}
        submitLabel={(staffId) => {
          const role = roleFromStaffId(staffId)
          return role ? `${t('v2.login.submit')} · ${stageName(role, lang)}` : t('v2.login.submit')
        }}
        demos={DEMO_STAFF_IDS.map((id) => ({ label: id, staffId: id }))}
        signIn={signInDepartment}
        onSignedIn={() => navigate('/department')}
      />
    </LoginShell>
  )
}
