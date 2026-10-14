import 'leaflet/dist/leaflet.css'

import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from 'react-leaflet'

import type { OperationsMetrics } from '@/api/types'
import { useLang } from '@/i18n'
import { percent } from '@/lib/format'
import { issueLabel } from '@/lib/issues'

type OfficeRow = OperationsMetrics['by_office'][number]

// Status colours (fill, stroke). Colour = this office's 7-day reject rate relative to the district rate.
const BANDS = [
  { min: 1.45, fill: '#dc2626', stroke: '#991b1b', key: 'admin.legend.high' },
  { min: 1.2, fill: '#d97706', stroke: '#92400e', key: 'admin.legend.mid' },
  { min: 0, fill: '#16a34a', stroke: '#166534', key: 'admin.legend.ok' },
] as const

function districtRate(rows: OfficeRow[]): number {
  const subs = rows.reduce((s, o) => s + o.submissions, 0)
  return subs ? rows.reduce((s, o) => s + o.reject_rate * o.submissions, 0) / subs : 0
}

function band(rate: number, district: number) {
  const ratio = district > 0 ? rate / district : 0
  return BANDS.find((b) => ratio >= b.min) ?? BANDS[BANDS.length - 1]
}

/** District map: one circle per office. Markers render even if map tiles fail to load (offline venue). */
export function OfficeMap({ week }: { week: OperationsMetrics | null }) {
  const { t } = useLang()
  const district = districtRate(week?.by_office ?? [])
  // Draw the hottest offices last so they sit on top (Sulur taluk office and Sulur 2 share almost one spot).
  const rows = [...(week?.by_office ?? [])].sort((a, b) => a.reject_rate - b.reject_rate)

  return (
    <div className="relative isolate h-[440px] overflow-hidden rounded-lg border bg-muted">
      <MapContainer center={[11.0, 76.96]} zoom={9} scrollWheelZoom={false} className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {rows.map((o) => {
          const b = band(o.reject_rate, district)
          return (
            <CircleMarker
              key={o.office_id}
              center={[o.lat, o.lng]}
              radius={6 + Math.sqrt(o.backlog) * 2.2}
              pathOptions={{ color: b.stroke, weight: 2, fillColor: b.fill, fillOpacity: 0.6 }}
            >
              <Tooltip direction="top">{o.office_name}</Tooltip>
              <Popup>
                <div className="space-y-1 text-sm">
                  <p className="font-semibold">{o.office_name}</p>
                  <p>
                    {t('admin.rejectRate')}: <b>{percent(o.reject_rate)}</b> (district {percent(district)})
                  </p>
                  <p>
                    {t('admin.kpi.backlog')}: <b>{o.backlog}</b> · {t('admin.submissions')}: {o.submissions}
                  </p>
                  {o.top_issue && (
                    <p>
                      {t('admin.topIssue')}: <b>{issueLabel(o.top_issue)}</b>
                    </p>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>
      <div className="pointer-events-none absolute bottom-2 left-2 z-[1000] space-y-1 rounded-md border bg-card/95 px-2.5 py-2 text-xs shadow-sm">
        {BANDS.map((b) => (
          <p key={b.key} className="flex items-center gap-1.5">
            <span className="inline-block size-3 rounded-full border-2" style={{ background: b.fill, borderColor: b.stroke }} />
            {t(b.key)}
          </p>
        ))}
        <p className="max-w-52 pt-0.5 text-muted-foreground">{t('admin.mapLegend')}</p>
      </div>
    </div>
  )
}
