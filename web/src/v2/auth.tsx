// Mock authentication only. No real credentials, Aadhaar numbers or payment details are ever
// captured or stored — this is a demo login that accepts any input and a one-click demo account.
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

import type { Stage } from '@/api/types'

export type CitizenProfile = {
  kind: 'citizen'
  name: string
  phone: string
  dob: string | null
}

export type DepartmentProfile = {
  kind: 'department'
  name: string
  role: Stage
}

export type Profile = CitizenProfile | DepartmentProfile

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
    loginDepartment: (p) => setProfile({ kind: 'department', ...p }),
    logout: () => setProfile(null),
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
