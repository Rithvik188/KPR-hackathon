import 'leaflet/dist/leaflet.css'

import { MapPin } from 'lucide-react'
import { useEffect, useState } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip } from 'react-leaflet'

import { getOffices } from '@/api/client'
import type { Office } from '@/api/types'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useLang } from '@/i18n'
import { Breadcrumbs } from '@/v2/components/Breadcrumbs'

export function CentresPage() {
  const { t } = useLang()
  const [offices, setOffices] = useState<Office[] | null>(null)

  useEffect(() => {
    getOffices().then(setOffices).catch(() => setOffices([]))
  }, [])

  return (
    <div className="space-y-5">
      <Breadcrumbs items={[{ label: t('v2.home.centres') }]} />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('v2.centres.title')}</h1>
        <p className="text-muted-foreground">{t('v2.centres.subtitle')}</p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="space-y-2 lg:max-h-[520px] lg:overflow-y-auto lg:pr-1">
          {offices === null &&
            Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-16 w-full" />)}
          {offices?.map((o) => (
            <Card key={o.id} className="py-0">
              <CardContent className="flex items-start gap-3 py-3">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-primary">
                  <MapPin className="size-4" aria-hidden />
                </span>
                <div>
                  <p className="font-medium">{o.name}</p>
                  <p className="text-xs text-muted-foreground">{t('v2.centres.directions', { taluk: o.taluk })}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="h-[420px] overflow-hidden rounded-lg border bg-muted lg:h-[520px]">
          <MapContainer center={[11.0, 76.96]} zoom={9} scrollWheelZoom={false} className="h-full w-full">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {offices?.map((o) => (
              <CircleMarker key={o.id} center={[o.lat, o.lng]} radius={7} pathOptions={{ color: '#0b5bb5', weight: 2, fillColor: '#0b5bb5', fillOpacity: 0.5 }}>
                <Tooltip direction="top">{o.name}</Tooltip>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  )
}
