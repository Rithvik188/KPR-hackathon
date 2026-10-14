// Mock authentication only. No real credentials, Aadhaar numbers, OTPs or payment details are ever sent
// anywhere or stored beyond this browser's localStorage — everything here is a demo login.
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

import type { Office, Stage } from '@/api/types'

export type CentreType = 'govt' | 'private'

export type CitizenProfile = {
  kind: 'citizen'
  name: string
  phone: string
  dob: string | null
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

/** The staff ID alone decides a department officer's role (e.g. VAO-SULUR-014 → vao). There is no role picker. */
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

/** A stored profile must still satisfy the sign-in rules: a department role has to match its staff ID, so an
 * edited localStorage entry (or one from the old free role picker) can't grant a higher stage. */
function isConsistent(p: Profile): boolean {
  if (p.kind === 'department') return roleFromStaffId(p.employeeId ?? '') === p.role
  if (p.kind === 'operator') return Boolean(p.officeId && p.employeeId)
  return true
}

function readProfile(): Profile | null {
  try {
    const raw = localStorage.getItem(KEY)
    const p = raw ? (JSON.parse(raw) as Profile) : null
    return p && isConsistent(p) ? p : null
  } catch {
    return null
  }
}

function writeProfile(p: Profile | null) {
  try {
    if (p) localStorage.setItem(KEY, JSON.stringify(p))
    else localStorage.removeItem(KEY)
  } catch {
    // storage unavailable: the session lasts for this tab only
  }
}

interface AuthContextValue {
  profile: Profile | null
  loginCitizen: (profile: Omit<CitizenProfile, 'kind'>) => void
  /** Returns false (and signs nobody in) if the staff ID doesn't parse. */
  loginDepartment: (input: { name: string; employeeId: string }) => boolean
  /** Returns false (and signs nobody in) if the office isn't an e-Sevai centre. */
  loginOperator: (input: { name: string; employeeId: string; office: Office }) => boolean
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(readProfile)

  useEffect(() => {
    writeProfile(profile)
  }, [profile])

  // Hierarchy is structural, not a preference: the role / centre type is derived here from the staff ID or the
  // office, callers can't pass one in, and nothing in the department/operator UI can change it afterwards.
  const value: AuthContextValue = {
    profile,
    loginCitizen: (p) => setProfile({ kind: 'citizen', ...p }),
    loginDepartment: ({ name, employeeId }) => {
      const id = employeeId.trim().toUpperCase()
      const role = roleFromStaffId(id)
      if (!role) return false
      setProfile({ kind: 'department', name, employeeId: id, role })
      return true
    },
    loginOperator: ({ name, employeeId, office }) => {
      const centreType = centreTypeOf(office)
      if (!centreType) return false
      setProfile({
        kind: 'operator',
        name,
        employeeId: employeeId.trim().toUpperCase(),
        centreType,
        officeId: office.id,
        officeName: office.name,
      })
      return true
    },
    logout: () => setProfile(null),
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
