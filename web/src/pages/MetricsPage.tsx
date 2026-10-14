// Metrics (P2-4): trust-first. Hero numbers on top (false-invalid rate, latency, projected rejection rate),
// then the per-issue table, field accuracy, latency, the consistency grid and the effectiveness projection.
// Every number comes from /api/metrics/detection (Person 1's held-out evaluation) or /api/metrics/operations.
import { ArrowRight, CircleAlert, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'

import { getDetectionMetrics, getOperationsMetrics } from '@/api/client'
import type { DetectionMetrics, OperationsMetrics } from '@/api/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { type I18nKey, useLang } from '@/i18n'
import { dateTime, percent, seconds } from '@/lib/format'
import { issueLabel } from '@/lib/issues'
import { cn } from '@/lib/utils'

function Hero({ value, label, hint, tone }: { value: React.ReactNode; label: string; hint: string; tone?: string }) {
  return (
    <Card className="gap-1 px-5 py-5">
      <p className={cn('text-4xl font-semibold tracking-tight tabular-nums', tone)}>{value}</p>
      <p className="font-medium">{label}</p>
      <p className="text-sm text-muted-foreground">{hint}</p>
    </Card>
  )
}

function Bar({ value, className }: { value: number; className?: string }) {
  return (
    <span className="inline-block h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <span className={cn('block h-full rounded-full bg-[var(--series-1)]', className)} style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
    </span>
  )
}

function PerCodeTable({ rows }: { rows: DetectionMetrics['per_code'] }) {
  const { t } = useLang()
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t('metrics.code')}</TableHead>
          <TableHead className="text-right">{t('metrics.precision')}</TableHead>
          <TableHead className="text-right">{t('metrics.recall')}</TableHead>
          <TableHead className="w-40">{t('metrics.f1')}</TableHead>
          <TableHead className="text-right">{t('metrics.support')}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((r) => (
          <TableRow key={r.code}>
            <TableCell>
              <span className="font-medium">{issueLabel(r.code)}</span>
              <span className="ml-2 font-mono text-[11px] text-muted-foreground">{r.code}</span>
            </TableCell>
            <TableCell className="text-right tabular-nums">{r.precision.toFixed(2)}</TableCell>
            <TableCell className="text-right tabular-nums">{r.recall.toFixed(2)}</TableCell>
            <TableCell>
              <span className="flex items-center gap-2">
                <Bar value={r.f1} />
                <span className="w-9 text-right tabular-nums">{r.f1.toFixed(2)}</span>
              </span>
            </TableCell>
            <TableCell className="text-right text-muted-foreground tabular-nums">{r.support}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

function FieldAccuracy({ m }: { m: DetectionMetrics }) {
  const { t } = useLang()
  const rows: [string, number][] = [
    [t('metrics.docType'), m.doc_type_accuracy],
    ['Aadhaar number', m.field_accuracy.aadhaar_number],
    ['PAN number', m.field_accuracy.pan_number],
    ['Voter ID (EPIC) number', m.field_accuracy.epic_number],
    [t('field.dob'), m.field_accuracy.dob],
    [t('field.name'), m.field_accuracy.name],
  ]
  return (
    <dl className="space-y-2.5">
      {rows.map(([label, value]) => (
        <div key={label} className="grid grid-cols-[minmax(0,1fr)_7rem_3.5rem] items-center gap-3 text-sm">
          <dt className="truncate">{label}</dt>
          <dd><Bar value={value ?? 0} /></dd>
          <dd className="text-right font-medium tabular-nums">{percent(value ?? 0, 1)}</dd>
        </div>
      ))}
    </dl>
  )
}

function LatencyTable({ l }: { l: DetectionMetrics['latency_ms'] }) {
  const { t } = useLang()
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead />
          <TableHead className="text-right">{t('metrics.p50')}</TableHead>
          <TableHead className="text-right">{t('metrics.p95')}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>{t('metrics.qualityPath')}</TableCell>
          <TableCell className="text-right tabular-nums">{l.quality_p50} ms</TableCell>
          <TableCell className="text-right tabular-nums">{l.quality_p95} ms</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>{t('metrics.fullPath')}</TableCell>
          <TableCell className="text-right tabular-nums">{seconds(l.full_p50)} s</TableCell>
          <TableCell className="text-right tabular-nums">{seconds(l.full_p95)} s</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  )
}

/** 3×3 confusion grid; one hue, darker = more sets. The diagonal is where the system agreed with the truth. */
function ConfusionGrid({ c }: { c: DetectionMetrics['consistency'] }) {
  const { t } = useLang()
  const max = Math.max(1, ...c.confusion.flat())
  const total = c.confusion.flat().reduce((a, b) => a + b, 0)
  const correct = c.confusion.reduce((s, row, i) => s + (row[i] ?? 0), 0)
  const label = (l: string) => t(`tier.${l}` as I18nKey).split(':')[0]
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-[auto_repeat(3,minmax(0,1fr))] gap-1 text-xs">
        <span className="self-end pr-2 text-muted-foreground">
          {t('metrics.actual')} ↓ / {t('metrics.predicted')} →
        </span>
        {c.labels.map((l) => (
          <span key={l} className="text-center font-medium text-muted-foreground">{label(l)}</span>
        ))}
        {c.confusion.map((row, i) => (
          <div key={c.labels[i]} className="contents">
            <span className="self-center pr-2 font-medium text-muted-foreground">{label(c.labels[i])}</span>
            {row.map((n, j) => (
              <span
                key={j}
                title={`${label(c.labels[i])} → ${label(c.labels[j])}: ${n}`}
                className={cn('flex h-12 items-center justify-center rounded-md text-base font-semibold tabular-nums',
                  n / max > 0.5 ? 'text-white' : 'text-foreground', i === j && 'ring-2 ring-primary/30')}
                style={{ background: n === 0 ? 'var(--muted)' : `color-mix(in oklab, var(--primary) ${Math.round(15 + (n / max) * 85)}%, white)` }}
              >
                {n}
              </span>
            ))}
          </div>
        ))}
      </div>
      <p className="text-sm text-muted-foreground">{t('metrics.correct', { c: correct, n: total })}</p>
    </div>
  )
}

function Effectiveness({ ops }: { ops: OperationsMetrics }) {
  const { t } = useLang()
  const p = ops.projection
  const bars = [
    { label: t('metrics.baseline'), value: p.baseline_reject_rate, color: 'bg-muted-foreground/50' },
    { label: t('metrics.projectedBar'), value: p.projected_reject_rate, color: 'bg-primary' },
  ]
  const max = Math.max(0.01, p.baseline_reject_rate)
  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <div className="space-y-4">
        {bars.map((b) => (
          <div key={b.label} className="space-y-1.5">
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span>{b.label}</span>
              <span className="text-lg font-semibold tabular-nums">{percent(b.value, 1)}</span>
            </div>
            <span className="block h-3 overflow-hidden rounded-full bg-muted">
              <span className={cn('block h-full rounded-full', b.color)} style={{ width: `${(b.value / max) * 100}%` }} />
            </span>
          </div>
        ))}
        <p className="text-sm">
          {t('metrics.prevented')}: <b className="tabular-nums">{p.prevented_rejections.toLocaleString('en-IN')}</b>
          <span className="text-muted-foreground"> / {ops.totals.applications.toLocaleString('en-IN')} applications, {ops.days} days</span>
        </p>
      </div>
      <div className="rounded-lg bg-accent/60 p-4 text-sm">
        <p className="mb-1 font-medium">{t('metrics.assumptions')}</p>
        <p className="text-muted-foreground">{p.assumptions_en}</p>
      </div>
    </div>
  )
}

export function MetricsPage() {
  const { t } = useLang()
  const [det, setDet] = useState<DetectionMetrics | null>(null)
  const [ops, setOps] = useState<OperationsMetrics | null>(null)

  useEffect(() => {
    Promise.all([getDetectionMetrics(), getOperationsMetrics(30)])
      .then(([d, o]) => {
        setDet(d)
        setOps(o)
      })
      .catch((err) => toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) }))
  }, [t])

  const fixture = det?.source === 'FIXTURE'

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t('metrics.title')}</h1>
          <p className="text-muted-foreground">{t('metrics.subtitle')}</p>
        </div>
        {det && !fixture && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-success-soft px-3 py-1 text-sm font-medium text-success">
            <ShieldCheck className="size-4" aria-hidden />
            {t('metrics.sourceEvaluation')} · {dateTime(det.generated_at)}
          </span>
        )}
      </div>
      {fixture && (
        <p className="flex items-center gap-2 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 font-medium text-danger">
          <CircleAlert className="size-4 shrink-0" aria-hidden />
          {t('metrics.fixtureWarning')}
        </p>
      )}

      {!det || !ops ? (
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }, (_, i) => <Skeleton key={i} className="h-36 rounded-xl" />)}
        </div>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Hero value={percent(det.false_invalid_rate, 1)} label={t('metrics.falseInvalid')}
                  hint={t('metrics.falseInvalidHint')} tone={det.false_invalid_rate === 0 ? 'text-success' : undefined} />
            <Hero value={`${seconds(det.latency_ms.full_p50)} s`} label={t('metrics.latency')}
                  hint={t('metrics.latencyHint', { q: det.latency_ms.quality_p50 })} />
            <Hero
              value={
                <span className="inline-flex items-center gap-2">
                  <span className="text-muted-foreground">{percent(ops.projection.baseline_reject_rate, 1)}</span>
                  <ArrowRight className="size-6 text-muted-foreground" aria-label="to" />
                  <span className="text-primary">{percent(ops.projection.projected_reject_rate, 1)}</span>
                </span>
              }
              label={t('metrics.projected')}
              hint={t('metrics.projectedHint', { n: ops.projection.prevented_rejections.toLocaleString('en-IN') })}
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
            <Card className="gap-3">
              <CardHeader>
                <CardTitle className="text-base">{t('metrics.perCode')}</CardTitle>
              </CardHeader>
              <CardContent>
                <PerCodeTable rows={det.per_code} />
              </CardContent>
            </Card>
            <Card className="gap-3">
              <CardHeader>
                <CardTitle className="text-base">{t('metrics.fields')}</CardTitle>
              </CardHeader>
              <CardContent>
                <FieldAccuracy m={det} />
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="gap-3">
              <CardHeader>
                <CardTitle className="text-base">{t('metrics.consistency')}</CardTitle>
              </CardHeader>
              <CardContent>
                <ConfusionGrid c={det.consistency} />
              </CardContent>
            </Card>
            <Card className="gap-3">
              <CardHeader>
                <CardTitle className="text-base">{t('metrics.latencyTable')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <LatencyTable l={det.latency_ms} />
                <div className="text-sm">
                  <p className="font-medium">{t('metrics.dataset')}</p>
                  <p className="text-muted-foreground">
                    {t('metrics.datasetCounts', { tune: det.dataset.tune_n, test: det.dataset.test_n, sets: det.dataset.sets_n })}
                  </p>
                  <p className="text-muted-foreground">{det.dataset.note_en}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="gap-4">
            <CardHeader>
              <CardTitle className="text-base">{t('metrics.effectiveness')}</CardTitle>
            </CardHeader>
            <CardContent>
              <Effectiveness ops={ops} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
