import { ChevronRight, Home } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePortalBase } from '@/v2/portalBase'

export interface Crumb {
  label: string
  to?: string
}

/** Every v2 page below home shows one of these, so the site reads as properly structured sub-pages. */
export function Breadcrumbs({ items, homeHref }: { items: Crumb[]; homeHref?: string }) {
  const base = usePortalBase()
  const home = homeHref ?? base
  return (
    <nav aria-label="Breadcrumb" className="mx-auto max-w-7xl px-4 pt-4">
      <ol className="flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
        <li className="flex items-center gap-1.5">
          <Link to={home} className="flex items-center gap-1 hover:text-foreground hover:underline">
            <Home className="size-3.5" aria-hidden />
            <span className="sr-only sm:not-sr-only">Home</span>
          </Link>
        </li>
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-1.5">
            <ChevronRight className="size-3.5" aria-hidden />
            {item.to && i < items.length - 1 ? (
              <Link to={item.to} className="hover:text-foreground hover:underline">
                {item.label}
              </Link>
            ) : (
              <span aria-current="page" className="font-medium text-foreground">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
