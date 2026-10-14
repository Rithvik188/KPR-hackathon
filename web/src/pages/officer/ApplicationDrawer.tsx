import { ImageOff, ShieldCheck } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

import { documentImageUrl, getApplication } from '@/api/client'
import type { ApplicationDetail, ApplicationDocument, DocType, Stage } from '@/api/types'
import { ConsistencyCard } from '@/components/ConsistencyCard'
import { FlagChips } from '@/components/FlagChips'
import { OfficerIssueList } from '@/components/IssueList'
import { FieldGrid } from '@/components/ResultCard'
import { SlaChip, StageSlaChip } from '@/components/SlaChip'
import { StageTrack } from '@/components/StageTrack'
import { AppStatusBadge, DocStatusBadge } from '@/components/StatusBadge'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import { useLang } from '@/i18n'
import { dateTime } from '@/lib/format'
import { issueLabel } from '@/lib/issues'
import { OfficerActions } from '@/pages/officer/OfficerActions'

function CardImage({ doc, decided }: { doc: ApplicationDocument; decided: boolean }) {
  const { t } = useLang()
  const [failed, setFailed] = useState(false)
  if (!doc.image_available || failed) {
    return (
      <div className="flex aspect-[1000/630] w-full flex-col items-center justify-center gap-1 rounded-md border border-dashed bg-muted p-2 text-center text-xs text-muted-foreground">
        {decided ? <ShieldCheck className="size-5 text-success" aria-hidden /> : <ImageOff className="size-5" aria-hidden />}
        {decided ? t('officer.imageDeleted') : t('officer.imageMissing')}
      </div>
    )
  }
  return (
    <img
      src={documentImageUrl(doc.id)}
      alt={doc.doc_type}
      onError={() => setFailed(true)}
      className="aspect-[1000/630] w-full rounded-md border bg-muted object-contain"
    />
  )
}

function DocumentCard({ doc, decided }: { doc: ApplicationDocument; decided: boolean }) {
  const { t } = useLang()
  return (
    <div className="grid gap-3 rounded-lg border bg-card p-3 sm:grid-cols-[220px_1fr]">
      <CardImage doc={doc} decided={decided} />
      <div className="min-w-0 space-y-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="font-medium">{t(`doc.${(doc.declared_type ?? doc.doc_type) as DocType}`)}</p>
          <DocStatusBadge status={doc.status} />
        </div>
        {doc.fields && <FieldGrid fields={doc.fields} />}
        <OfficerIssueList issues={doc.issues} />
      </div>
    </div>
  )
}

function humanize(event: string): string {
  const text = event.replaceAll('_', ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2.5">
      <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{title}</h3>
      {children}
    </section>
  )
}

/** Wide right-hand drawer: card images, read fields, explainable issues, consistency, history and actions. */
export function ApplicationDrawer({
  applicationId,
  role,
  onClose,
  onChanged,
}: {
  applicationId: string | null
  role: Stage | null
  onClose: () => void
  onChanged: () => void
}) {
  const { t } = useLang()
  const [detail, setDetail] = useState<ApplicationDetail | null>(null)
  // Parent passes a fresh onClose each render; keep the latest in a ref so `load` only changes with the id.
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  const load = useCallback(async () => {
    if (!applicationId) return
    try {
      setDetail(await getApplication(applicationId))
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
      onCloseRef.current()
    }
  }, [applicationId, t])

  useEffect(() => {
    setDetail(null)
    load()
  }, [load])

  const decided = detail?.status === 'approved' || detail?.status === 'rejected'

  return (
    <Sheet open={applicationId !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="gap-0 p-0 data-[side=right]:w-full data-[side=right]:sm:max-w-2xl">
        <SheetHeader className="space-y-2 border-b p-5 pr-12">
          {detail ? (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <SheetTitle className="text-lg">{detail.citizen_name}</SheetTitle>
                <AppStatusBadge status={detail.status} />
              </div>
              <SheetDescription className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="font-mono text-xs">{detail.id}</span>
                <span>{detail.office_name}</span>
                <span>{t(`service.${detail.service}`)}</span>
                <span>{detail.phone_masked}</span>
                {detail.can_id && <span className="font-mono text-xs">CAN {detail.can_id}</span>}
              </SheetDescription>
              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                <SlaChip hoursLeft={detail.sla_hours_left} status={detail.status} />
                {detail.stage && <StageSlaChip hoursLeft={detail.stage_sla_hours_left} />}
                <span>
                  {t('officer.created')} {dateTime(detail.created_at)}
                </span>
                <span>
                  {t('officer.resubmissions')}: {detail.resubmissions}
                </span>
              </div>
              {detail.flag_codes.length > 0 && <FlagChips codes={detail.flag_codes} />}
              {(detail.stage || detail.status === 'approved') && <StageTrack stage={detail.stage} status={detail.status} />}
            </>
          ) : (
            <>
              <SheetTitle className="sr-only">{applicationId}</SheetTitle>
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-72" />
            </>
          )}
        </SheetHeader>

        <div className="flex-1 space-y-6 overflow-y-auto p-5">
          {!detail ? (
            <div className="space-y-3">
              <Skeleton className="h-36 w-full" />
              <Skeleton className="h-36 w-full" />
            </div>
          ) : (
            <>
              <Section title={t('officer.documents')}>
                <div className="space-y-3">
                  {detail.documents.map((doc) => (
                    <DocumentCard key={doc.id} doc={doc} decided={decided} />
                  ))}
                </div>
              </Section>

              <Section title={t('consistency.title')}>
                <ConsistencyCard consistency={detail.consistency} />
                <OfficerIssueList issues={detail.consistency.issues} />
              </Section>

              {detail.decision && (
                <Section title={t('officer.decision')}>
                  <div className="rounded-lg border bg-card p-3 text-sm">
                    <p className="font-medium">
                      {t(detail.decision.action === 'approve' ? 'app.approved' : 'app.rejected')} ·{' '}
                      {dateTime(detail.decision.at)}
                    </p>
                    {detail.decision.reason_code && (
                      <p className="text-muted-foreground">{issueLabel(detail.decision.reason_code)}</p>
                    )}
                    {detail.decision.note && <p className="text-muted-foreground">“{detail.decision.note}”</p>}
                  </div>
                </Section>
              )}

              <Section title={t('officer.history')}>
                <ol className="relative space-y-3 border-l pl-4">
                  {detail.history.map((h, i) => (
                    <li key={i} className="relative">
                      <span className="absolute top-1.5 -left-[21px] size-2.5 rounded-full border-2 border-card bg-primary" />
                      <p className="text-sm">
                        <span className="font-medium">{humanize(h.event)}</span>
                        <span className="ml-2 text-xs text-muted-foreground">
                          {h.actor} · {dateTime(h.at)}
                        </span>
                      </p>
                      {h.note && <p className="text-xs text-muted-foreground">{h.note}</p>}
                    </li>
                  ))}
                </ol>
              </Section>
            </>
          )}
        </div>

        {detail && !decided && (
          <div className="border-t bg-card p-4">
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">{t('officer.actions')}</p>
            <OfficerActions
              applicationId={detail.id}
              stage={detail.stage ?? null}
              status={detail.status}
              role={role}
              onDone={() => {
                load()
                onChanged()
              }}
            />
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}
