import { useLocation } from 'react-router-dom'

export type PortalBase = '/portal' | '/operator' | '/department'

/** Which portal the current page is rendered in. Pages shared by the citizen and operator portals use it so
 * their links stay inside the signed-in portal instead of bouncing to another login. */
export function usePortalBase(): PortalBase {
  const { pathname } = useLocation()
  if (pathname.startsWith('/operator')) return '/operator'
  if (pathname.startsWith('/department')) return '/department'
  return '/portal'
}
