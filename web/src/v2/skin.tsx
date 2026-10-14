// Scopes every v2 route to the esevai theme tokens (src/index.css) by stamping data-skin on <html>.
// v1 (/classic/*) never renders this, so it keeps the default gov-trust tokens.
import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

export function EsevaiSkin() {
  const location = useLocation()
  useEffect(() => {
    document.documentElement.dataset.skin = 'esevai'
    return () => {
      delete document.documentElement.dataset.skin
    }
  }, [])
  // Scroll to top on route change, like a real multi-page portal.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [location.pathname])
  return null
}
