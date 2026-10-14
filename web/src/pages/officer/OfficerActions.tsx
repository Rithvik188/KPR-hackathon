import { CircleCheck, CircleX, Undo2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { actOnApplication } from '@/api/client'
import type { OfficerAction } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useLang } from '@/i18n'
import { issueLabel, REASON_CODES } from '@/lib/issues'

/** Approve in one click; Request fix and Reject open a reason (and note) form first. */
export function OfficerActions({ applicationId, onDone }: { applicationId: string; onDone: () => void }) {
  const { t } = useLang()
  const [mode, setMode] = useState<'request_fix' | 'reject' | null>(null)
  const [reason, setReason] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)

  async function act(action: OfficerAction) {
    setBusy(true)
    try {
      await actOnApplication(applicationId, {
        action,
        reason_code: action === 'approve' ? null : reason,
        note: note.trim() || null,
      })
      toast.success(t(`officer.done.${action}`))
      setMode(null)
      setReason('')
      setNote('')
      onDone()
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setBusy(false)
    }
  }

  if (mode === null) {
    return (
      <div className="flex flex-wrap gap-2">
        <Button size="lg" disabled={busy} onClick={() => act('approve')} className="bg-success text-white hover:bg-success/90">
          <CircleCheck aria-hidden />
          {t('officer.approve')}
        </Button>
        <Button size="lg" variant="outline" disabled={busy} onClick={() => setMode('request_fix')}>
          <Undo2 aria-hidden />
          {t('officer.requestFix')}
        </Button>
        <Button size="lg" variant="outline" disabled={busy} onClick={() => setMode('reject')} className="text-danger hover:text-danger">
          <CircleX aria-hidden />
          {t('officer.reject')}
        </Button>
      </div>
    )
  }

  const needsNote = mode === 'reject'
  const canConfirm = reason !== '' && (!needsNote || note.trim() !== '')

  return (
    <div className="space-y-3 animate-in duration-150 fade-in">
      <p className="text-sm font-medium">{mode === 'reject' ? t('officer.reject') : t('officer.requestFix')}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="reason">{t('officer.reason')}</Label>
          <Select value={reason} onValueChange={setReason}>
            <SelectTrigger id="reason" className="w-full">
              <SelectValue placeholder={t('officer.chooseReason')} />
            </SelectTrigger>
            <SelectContent>
              {REASON_CODES.map((code) => (
                <SelectItem key={code} value={code}>
                  {issueLabel(code)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="note">{needsNote ? t('officer.noteRequired') : t('officer.note')}</Label>
          <Textarea id="note" rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          disabled={busy || !canConfirm}
          onClick={() => act(mode)}
          variant={mode === 'reject' ? 'destructive' : 'default'}
        >
          {t('officer.confirm')}
        </Button>
        <Button variant="ghost" disabled={busy} onClick={() => setMode(null)}>
          {t('officer.cancel')}
        </Button>
      </div>
    </div>
  )
}
