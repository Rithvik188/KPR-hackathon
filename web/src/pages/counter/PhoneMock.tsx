import { MessageSquare } from 'lucide-react'
import { useEffect, useState } from 'react'

import { listNotifications } from '@/api/client'
import type { Notification } from '@/api/types'
import { useLang } from '@/i18n'
import { timeOnly } from '@/lib/format'

const POLL_MS = 3000

/** A phone frame showing the mock SMS sent to the citizen for this application (polled every 3 s). */
export function PhoneMock({ applicationId, phoneMasked }: { applicationId: string; phoneMasked: string }) {
  const { t } = useLang()
  const [messages, setMessages] = useState<Notification[]>([])

  useEffect(() => {
    let cancelled = false
    const load = () =>
      listNotifications(applicationId)
        .then((list) => !cancelled && setMessages(list))
        .catch(() => {
          // transient network error: the next poll retries
        })
    load()
    const timer = setInterval(load, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [applicationId])

  return (
    <div className="mx-auto w-full max-w-[300px] rounded-[2.25rem] border-[10px] border-slate-800 bg-slate-800 shadow-lg">
      <div className="overflow-hidden rounded-[1.6rem] bg-slate-100">
        <div className="flex items-center gap-2 border-b bg-white px-4 pt-5 pb-3">
          <MessageSquare className="size-4 text-primary" aria-hidden />
          <div className="leading-tight">
            <p className="text-sm font-semibold">SevaiCheck</p>
            <p className="text-xs text-muted-foreground">
              {t('counter.phoneTitle')} · {phoneMasked}
            </p>
          </div>
        </div>
        <div className="flex h-[340px] flex-col-reverse gap-3 overflow-y-auto p-3" aria-live="polite">
          {messages.length === 0 && <p className="m-auto text-sm text-muted-foreground">{t('counter.noSms')}</p>}
          {messages.map((m) => (
            <div key={m.id} className="max-w-[92%] animate-in rounded-2xl rounded-tl-sm bg-white p-3 shadow-sm duration-200 fade-in slide-in-from-bottom-1">
              <p lang="ta" className="font-tamil text-sm leading-snug">
                {m.body_ta}
              </p>
              <p lang="en" className="mt-1.5 text-xs leading-snug text-muted-foreground">
                {m.body_en}
              </p>
              <p className="mt-1 text-right text-[10px] text-muted-foreground">{timeOnly(m.created_at)}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
