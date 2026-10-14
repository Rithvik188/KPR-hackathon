// Admin charts. One y-axis per chart (backlog has its own chart rather than a second axis), thin 2px lines,
// recessive grid, legend for multi-series, hover tooltips, and a table view (aqua is below 3:1 on white).
import { useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { OperationsMetrics } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useLang } from '@/i18n'
import { issueLabel } from '@/lib/issues'

type Daily = OperationsMetrics['daily']

const AXIS = { stroke: 'var(--muted-foreground)', fontSize: 11, tickLine: false, axisLine: false } as const
const TOOLTIP = {
  contentStyle: { borderRadius: 8, border: '1px solid var(--border)', fontSize: 12, boxShadow: '0 4px 12px rgb(0 0 0 / 0.08)' },
  labelStyle: { color: 'var(--foreground)', fontWeight: 600 },
} as const

function shortDate(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

function ChartSkeleton() {
  return <Skeleton className="h-[260px] w-full" />
}

export function DailyFlowChart({ daily }: { daily: Daily | null }) {
  const { t } = useLang()
  const [showTable, setShowTable] = useState(false)
  const series = [
    { key: 'submitted', name: t('admin.submitted'), color: 'var(--series-1)' },
    { key: 'approved', name: t('admin.approvedSeries'), color: 'var(--series-2)' },
    { key: 'rejected', name: t('admin.rejectedSeries'), color: 'var(--series-3)' },
  ] as const

  return (
    <Card className="gap-3">
      <CardHeader>
        <CardTitle className="text-base">{t('admin.daily')}</CardTitle>
        <CardAction>
          <Button variant="ghost" size="sm" onClick={() => setShowTable((v) => !v)}>
            {showTable ? t('admin.hideTable') : t('admin.showTable')}
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {!daily ? (
          <ChartSkeleton />
        ) : showTable ? (
          <div className="max-h-[260px] overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('admin.date')}</TableHead>
                  {series.map((s) => (
                    <TableHead key={s.key} className="text-right">
                      {s.name}
                    </TableHead>
                  ))}
                  <TableHead className="text-right">{t('admin.backlog')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[...daily].reverse().map((d) => (
                  <TableRow key={d.date}>
                    <TableCell>{shortDate(d.date)}</TableCell>
                    <TableCell className="text-right tabular-nums">{d.submitted}</TableCell>
                    <TableCell className="text-right tabular-nums">{d.approved}</TableCell>
                    <TableCell className="text-right tabular-nums">{d.rejected}</TableCell>
                    <TableCell className="text-right tabular-nums">{d.backlog}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={daily} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
              <CartesianGrid vertical={false} stroke="var(--grid)" />
              <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={24} {...AXIS} />
              <YAxis allowDecimals={false} {...AXIS} />
              <Tooltip labelFormatter={(v) => shortDate(String(v))} {...TOOLTIP} />
              <Legend iconType="plainline" itemSorter={null} wrapperStyle={{ fontSize: 12 }} />
              {series.map((s) => (
                <Line key={s.key} type="monotone" dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={2}
                      dot={false} activeDot={{ r: 4, strokeWidth: 2, stroke: 'var(--card)' }} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

export function BacklogChart({ daily }: { daily: Daily | null }) {
  const { t } = useLang()
  return (
    <Card className="gap-3">
      <CardHeader>
        <CardTitle className="text-base">{t('admin.backlog')}</CardTitle>
      </CardHeader>
      <CardContent>
        {!daily ? (
          <ChartSkeleton />
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={daily} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
              <CartesianGrid vertical={false} stroke="var(--grid)" />
              <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={24} {...AXIS} />
              <YAxis allowDecimals={false} {...AXIS} />
              <Tooltip labelFormatter={(v) => shortDate(String(v))} {...TOOLTIP} />
              <Area type="monotone" dataKey="backlog" name={t('admin.backlog')} stroke="var(--primary)" strokeWidth={2}
                    fill="var(--primary)" fillOpacity={0.08} activeDot={{ r: 4, strokeWidth: 2, stroke: 'var(--card)' }} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

export function IssuesChart({ byIssue }: { byIssue: OperationsMetrics['by_issue'] | null }) {
  const { t } = useLang()
  const data = (byIssue ?? []).slice(0, 9).map((d) => ({ ...d, label: issueLabel(d.code) }))
  return (
    <Card className="gap-3">
      <CardHeader>
        <CardTitle className="text-base">{t('admin.byIssue')}</CardTitle>
      </CardHeader>
      <CardContent>
        {!byIssue ? (
          <ChartSkeleton />
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(160, data.length * 30)}>
            <BarChart data={data} layout="vertical" margin={{ top: 0, right: 40, bottom: 0, left: 8 }} barCategoryGap={6}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="label" width={150} {...AXIS} />
              <Tooltip cursor={{ fill: 'var(--muted)' }} {...TOOLTIP} />
              <Bar dataKey="count" name="Applications" fill="var(--series-1)" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="count" position="right" fontSize={11} fill="var(--muted-foreground)" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
