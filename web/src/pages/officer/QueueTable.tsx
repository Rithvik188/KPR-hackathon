import type { ApplicationSummary } from '@/api/types'
import { FlagChips } from '@/components/FlagChips'
import { SlaChip } from '@/components/SlaChip'
import { AppStatusBadge } from '@/components/StatusBadge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useLang } from '@/i18n'
import { cn } from '@/lib/utils'

export function QueueTable({
  items,
  loading,
  selectedId,
  onSelect,
}: {
  items: ApplicationSummary[]
  loading: boolean
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const { t } = useLang()

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t('officer.status')}</TableHead>
          <TableHead>{t('officer.citizen')}</TableHead>
          <TableHead className="hidden md:table-cell">{t('officer.office')}</TableHead>
          <TableHead className="hidden lg:table-cell">{t('officer.service')}</TableHead>
          <TableHead>{t('officer.flags')}</TableHead>
          <TableHead>{t('officer.sla')}</TableHead>
          <TableHead className="hidden text-right sm:table-cell">{t('officer.docs')}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {loading && items.length === 0
          ? Array.from({ length: 6 }, (_, i) => (
              <TableRow key={i}>
                <TableCell colSpan={7}>
                  <Skeleton className="h-6 w-full" />
                </TableCell>
              </TableRow>
            ))
          : items.map((app) => (
              <TableRow
                key={app.id}
                onClick={() => onSelect(app.id)}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelect(app.id)}
                tabIndex={0}
                aria-selected={selectedId === app.id}
                className={cn('cursor-pointer', selectedId === app.id && 'bg-accent/60 hover:bg-accent/60')}
              >
                <TableCell>
                  <AppStatusBadge status={app.status} />
                </TableCell>
                <TableCell>
                  <p className="font-medium">{app.citizen_name}</p>
                  <p className="font-mono text-[11px] text-muted-foreground">{app.id}</p>
                </TableCell>
                <TableCell className="hidden text-muted-foreground md:table-cell">{app.office_name}</TableCell>
                <TableCell className="hidden text-muted-foreground lg:table-cell">{t(`service.${app.service}`)}</TableCell>
                <TableCell className="max-w-56">
                  <FlagChips codes={app.flag_codes} />
                </TableCell>
                <TableCell>
                  <SlaChip hoursLeft={app.sla_hours_left} status={app.status} />
                </TableCell>
                <TableCell className="hidden text-right tabular-nums sm:table-cell">{app.doc_count}/3</TableCell>
              </TableRow>
            ))}
        {!loading && items.length === 0 && (
          <TableRow>
            <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
              {t('officer.empty')}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  )
}
