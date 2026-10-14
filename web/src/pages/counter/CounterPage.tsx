// Counter (P2-2): operator bar → three document slots → application panel + phone mock.
// Tuned for a projected laptop; stacks to one column on a phone.
import { useState } from 'react'

import type { ApplicationSummary, ConsistencyResult, UploadResult } from '@/api/types'
import { useLang } from '@/i18n'
import { ApplicationPanel } from '@/pages/counter/ApplicationPanel'
import { DocSlot, type SlotName } from '@/pages/counter/DocSlot'
import { OperatorBar } from '@/pages/counter/OperatorBar'
import { PhoneMock } from '@/pages/counter/PhoneMock'

const SLOTS: SlotName[] = ['aadhaar_front', 'aadhaar_back', 'id_proof']

export function CounterPage() {
  const { t } = useLang()
  const [application, setApplication] = useState<ApplicationSummary | null>(null)
  const [consistency, setConsistency] = useState<ConsistencyResult | null>(null)

  function onUploaded(res: UploadResult) {
    setApplication(res.application)
    setConsistency(res.consistency)
  }

  function reset() {
    setApplication(null)
    setConsistency(null)
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('counter.title')}</h1>
        <p className="text-muted-foreground">{t('counter.subtitle')}</p>
      </div>

      <OperatorBar application={application} onCreated={setApplication} onReset={reset} />

      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
        <section className="space-y-4" aria-label={t('counter.documents')}>
          {!application && <p className="text-sm text-muted-foreground">{t('counter.createFirst')}</p>}
          {/* key: a new application remounts the slots, clearing their attempt history */}
          {SLOTS.map((slot) => (
            <DocSlot key={`${application?.id ?? 'none'}-${slot}`} slot={slot} applicationId={application?.id ?? null} onUploaded={onUploaded} />
          ))}
        </section>

        {application && (
          <aside className="space-y-5 lg:sticky lg:top-20">
            <ApplicationPanel application={application} consistency={consistency} />
            <PhoneMock applicationId={application.id} phoneMasked={application.phone_masked} />
          </aside>
        )}
      </div>
    </div>
  )
}
