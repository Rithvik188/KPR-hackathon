// Officer queue (P2-2): filters, the contract-sorted queue and a side drawer per application.
// `?app=<id>` opens that application's drawer directly (the counter's "Open in officer view" link).
import { RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { getOffices, listApplications } from '@/api/client'
import type { ApplicationList, AppStatus, Office } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useLang } from '@/i18n'
import { cn } from '@/lib/utils'
import { ApplicationDrawer } from '@/pages/officer/ApplicationDrawer'
import { QueueTable } from '@/pages/officer/QueueTable'

const PAGE = 50
const POLL_MS = 10_000
const STATUSES: AppStatus[] = ['ready_for_officer', 'needs_fix', 'submitted', 'approved', 'rejected']
const ALL = 'all'

export function OfficerPage() {
  const { t } = useLang()
  const [params, setParams] = useSearchParams()
  const selectedId = params.get('app')
  const [status, setStatus] = useState<string>('ready_for_officer')
  const [officeId, setOfficeId] = useState<string>(ALL)
  const [offset, setOffset] = useState(0)
  const [offices, setOffices] = useState<Office[]>([])
  const [data, setData] = useState<ApplicationList>({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOffices().then(setOffices).catch(() => {})
  }, [])

  const load = useCallback(
    async (quiet = false) => {
      if (!quiet) setLoading(true)
      try {
        setData(
          await listApplications({
            status: status === ALL ? undefined : (status as AppStatus),
            office_id: officeId === ALL ? undefined : officeId,
            limit: PAGE,
            offset,
          }),
        )
      } catch (err) {
        if (!quiet) toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
      } finally {
        setLoading(false)
      }
    },
    [status, officeId, offset, t],
  )

  useEffect(() => {
    load()
    const timer = setInterval(() => load(true), POLL_MS)
    return () => clearInterval(timer)
  }, [load])

  function select(id: string | null) {
    const next = new URLSearchParams(params)
    if (id) next.set('app', id)
    else next.delete('app')
    setParams(next, { replace: true })
  }

  const from = data.total === 0 ? 0 : offset + 1
  const to = Math.min(offset + PAGE, data.total)

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t('officer.title')}</h1>
          <p className="text-muted-foreground">{t('officer.subtitle')}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={status}
            onValueChange={(v) => {
              setStatus(v)
              setOffset(0)
            }}
          >
            <SelectTrigger className="w-48" aria-label={t('officer.status')}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>{t('officer.allStatuses')}</SelectItem>
              {STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {t(`app.${s}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={officeId}
            onValueChange={(v) => {
              setOfficeId(v)
              setOffset(0)
            }}
          >
            <SelectTrigger className="w-60" aria-label={t('officer.office')}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>{t('officer.allOffices')}</SelectItem>
              {offices.map((o) => (
                <SelectItem key={o.id} value={o.id}>
                  {o.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={() => load()} aria-label={t('officer.refresh')}>
            <RefreshCw className={cn(loading && 'animate-spin')} aria-hidden />
          </Button>
        </div>
      </div>

      <Card className="py-0">
        <QueueTable items={data.items} loading={loading} selectedId={selectedId} onSelect={select} />
      </Card>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span className="tabular-nums">{t('officer.showing', { from, to, total: data.total })}</span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
            {t('officer.prev')}
          </Button>
          <Button variant="outline" size="sm" disabled={to >= data.total} onClick={() => setOffset(offset + PAGE)}>
            {t('officer.next')}
          </Button>
        </div>
      </div>

      <ApplicationDrawer applicationId={selectedId} onClose={() => select(null)} onChanged={() => load(true)} />
    </div>
  )
}
