// Sign-in state for the three portals. Since contract v1.8 the server authenticates: staff sign in with ID and
// password, citizens with an OTP, and the server's signed token (src/api/session.ts) is sent on every API call.
// The role and centre shown here are copied from the server's answer, never chosen or typed in the browser.
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { toast } from 'sonner'

import { ApiError, getOffices, loginStaff, verifyOtp } from '@/api/client'
import { clearSession, getSession, onSessionExpired, setSession } from '@/api/session'
import type { Office, Session, Stage } from '@/api/types'
import { type I18nKey, useLang } from '@/i18n'

export type CentreType = 'govt' | 'private'

export type CitizenProfile = {
  kind: 'citizen'
  name: string
  phone: string
  dob: string | null
  /** v1.5: set once the citizen's CAN has been found or created, so later applications reuse it */
  can?: string | null
}

export type DepartmentProfile = {
  kind: 'department'
  name: string
  employeeId: string
  role: Stage
}

export type OperatorProfile = {
  kind: 'operator'
  name: string
  employeeId: string
  centreType: CentreType
  officeId: string
  officeName: string
}

export type Profile = CitizenProfile | DepartmentProfile | OperatorProfile

const STAFF_ID = /^(VAO|RI|TAH)-[A-Z]{3,}-\d{3}$/
const PREFIX_ROLE: Record<string, Stage> = { VAO: 'vao', RI: 'ri', TAH: 'tahsildar' }

/** A hint only, for the sign-in form ("Signing in as VAO"). The role that counts comes from the server. */
export function roleFromStaffId(staffId: string): Stage | null {
  const m = STAFF_ID.exec(staffId.trim().toUpperCase())
  return m ? PREFIX_ROLE[m[1]] : null
}

/** Govt vs private comes from the office's own type, never from the operator. */
export function centreTypeOf(office: Pick<Office, 'type'>): CentreType | null {
  if (office.type === 'esevai_centre') return 'govt'
  if (office.type === 'esevai_centre_private') return 'private'
  return null
}

const KEY = 'sevaicheck.v2.profile'

/** A stored profile is only used together with a live session that agrees with it, so editing storage can't
 * grant a different role or centre (and the server would refuse anyway). */
function matchesSession(p: Profile, s: Session | null): boolean {
  if (!s) return false
  if (p.kind === 'citizen') return s.role === 'citizen'
  if (p.kind === 'department') return s.role === p.role
  return s.role === 'operator' && s.office_id === p.officeId
}

function readProfile(): Profile | null {
  try {
    localStorage.removeItem(KEY) // profiles were kept in localStorage before v1.8; sign-ins now end with the tab
    const raw = sessionStorage.getItem(KEY)
    const p = raw ? (JSON.parse(raw) as Profile) : null
    return p && matchesSession(p, getSession()) ? p : null
  } catch {
    return null
  }
}

function writeProfile(p: Profile | null) {
  try {
    if (p) sessionStorage.setItem(KEY, JSON.stringify(p))
    else sessionStorage.removeItem(KEY)
  } catch {
    // storage unavailable: the sign-in lasts until this page is reloaded
  }
}

const STAFF_ROLES: readonly string[] = ['vao', 'ri', 'tahsildar']

interface AuthContextValue {
  profile: Profile | null
  /** Officer sign-in. Throws ApiError (BAD_CREDENTIALS, TOO_MANY_ATTEMPTS, WRONG_PORTAL, ...). */
  signInDepartment: (staffId: string, password: string) => Promise<void>
  /** e-Sevai operator sign-in; the centre is the one on the operator's account. */
  signInOperator: (staffId: string, password: string) => Promise<void>
  /** Citizen sign-in with the OTP from POST /auth/otp/request. */
  signInCitizen: (citizen: { name: string; phone: string; dob: string | null }, otp: string) => Promise<void>
  /** Remember the signed-in citizen's CAN (no-op for other profiles). */
  rememberCan: (can: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const { t } = useLang()
  const [profile, setProfile] = useState<Profile | null>(readProfile)

  useEffect(() => {
    writeProfile(profile)
  }, [profile])

  // The server rejected the token (expired, or the server restarted with a new key): drop the profile, and
  // <RequireAuth> sends the user to the login page of the portal they were in.
  useEffect(
    () =>
      onSessionExpired(() => {
        setProfile(null)
        toast.info(t('v2.session.expired'), { id: 'session-expired' }) // several calls may fail at once
      }),
    [t],
  )

  function start(session: Session, next: Profile) {
    setSession(session)
    setProfile(next)
  }

  const value: AuthContextValue = {
    profile,
    signInDepartment: async (staffId, password) => {
      const session = await loginStaff(staffId, password)
      if (!STAFF_ROLES.includes(session.role)) throw new ApiError(403, 'WRONG_PORTAL', 'Not a department account')
      start(session, {
        kind: 'department',
        name: session.name ?? staffId,
        employeeId: staffId.trim().toUpperCase(),
        role: session.role as Stage,
      })
    },
    signInOperator: async (staffId, password) => {
      const session = await loginStaff(staffId, password)
      if (session.role !== 'operator' || !session.office_id) {
        throw new ApiError(403, 'WRONG_PORTAL', 'Not an e-Sevai operator account')
      }
      const office = (await getOffices()).find((o) => o.id === session.office_id)
      const centreType = office ? centreTypeOf(office) : null
      if (!office || !centreType) throw new ApiError(404, 'OFFICE_NOT_FOUND', 'Your e-Sevai centre was not found')
      start(session, {
        kind: 'operator',
        name: session.name ?? staffId,
        employeeId: staffId.trim().toUpperCase(),
        centreType,
        officeId: office.id,
        officeName: office.name,
      })
    },
    signInCitizen: async ({ name, phone, dob }, otp) => {
      const session = await verifyOtp(phone, otp)
      start(session, { kind: 'citizen', name, phone, dob })
    },
    rememberCan: (can) => setProfile((p) => (p?.kind === 'citizen' ? { ...p, can } : p)),
    logout: () => {
      clearSession()
      setProfile(null)
    },
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}

/** A bilingual message for a failed sign-in, by the server's error code. */
export function signInErrorKey(err: unknown): I18nKey {
  const code = err instanceof ApiError ? err.code : ''
  if (code === 'BAD_CREDENTIALS') return 'v2.login.badCredentials'
  if (code === 'BAD_OTP') return 'v2.login.otpWrong'
  if (code === 'INVALID_PHONE') return 'v2.login.phoneInvalid'
  if (code === 'TOO_MANY_ATTEMPTS' || code === 'TOO_MANY_REQUESTS') return 'v2.login.tooMany'
  if (code === 'WRONG_PORTAL') return 'v2.login.wrongPortal'
  if (code === 'NETWORK_ERROR') return 'v2.login.network'
  return 'v2.login.failed'
}
