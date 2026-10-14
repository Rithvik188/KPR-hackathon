import { Navigate, Outlet } from 'react-router-dom'

import { useAuth, type Profile } from '@/v2/auth'

/** Gates a route subtree behind a signed-in profile of the given kind, redirecting to its login otherwise. */
export function RequireAuth({ kind, loginPath }: { kind: Profile['kind']; loginPath: string }) {
  const { profile } = useAuth()
  if (!profile || profile.kind !== kind) return <Navigate to={loginPath} replace />
  return <Outlet />
}
