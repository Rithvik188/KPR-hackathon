// Mock authentication only. No real credentials, Aadhaar numbers, OTPs or payment details are ever sent
// anywhere or stored beyond this browser's localStorage — everything here is a demo login.
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

import type { Stage } from '@/api/types'

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
  // TODO(handoff): required once DepartmentLoginPage is rewritten to collect a staff ID (see P2-TODO.md).
  employeeId?: string
  role: Stage
}

export type OperatorProfile = {
  kind: 'operator'
  name: string
  employeeId?: string
  centreType: CentreType
  officeId: string
  officeName: string
}

export type Profile = CitizenProfile | DepartmentProfile | OperatorProfile

const KEY = 'sevaicheck.v2.profile'

function readProfile(): Profile | null {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as Profile) : null
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
  loginDepartment: (profile: Omit<DepartmentProfile, 'kind'>) => void
  loginOperator: (profile: Omit<OperatorProfile, 'kind'>) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(readProfile)

  useEffect(() => {
    writeProfile(profile)
  }, [profile])

  const value: AuthContextValue = {
    profile,
    loginCitizen: (p) => setProfile({ kind: 'citizen', ...p }),
    // Hierarchy is structural, not a preference: the role/centre type is fixed at sign-in from the staff ID
    // or the selected office, and nothing in the department/operator UI can change it afterwards.
    loginDepartment: (p) => setProfile({ kind: 'department', ...p }),
    loginOperator: (p) => setProfile({ kind: 'operator', ...p }),
    logout: () => setProfile(null),
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
