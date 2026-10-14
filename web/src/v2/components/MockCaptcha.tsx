import { CircleCheck, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useLang } from '@/i18n'

function newPuzzle() {
  return { a: 1 + Math.floor(Math.random() * 9), b: 1 + Math.floor(Math.random() * 9) }
}

/** Prototype CAPTCHA: a random "a + b" checked in the browser. Never wire a real captcha service in here. */
export function MockCaptcha({ onSolvedChange }: { onSolvedChange: (solved: boolean) => void }) {
  const { t } = useLang()
  const [puzzle, setPuzzle] = useState(newPuzzle)
  const [answer, setAnswer] = useState('')
  const solved = answer.trim() !== '' && Number(answer) === puzzle.a + puzzle.b

  useEffect(() => {
    onSolvedChange(solved)
  }, [solved, onSolvedChange])

  function refresh() {
    setPuzzle(newPuzzle())
    setAnswer('')
  }

  return (
    <div className="space-y-1.5">
      <Label htmlFor="captcha-answer">{t('v2.login.captcha')}</Label>
      <div className="flex items-center gap-2">
        <span
          className="flex h-9 shrink-0 items-center rounded-md border border-dashed bg-muted px-3 font-mono text-sm tracking-widest select-none"
          aria-live="polite"
        >
          {t('v2.login.captchaQuestion', { a: puzzle.a, b: puzzle.b })}
        </span>
        <Input
          id="captcha-answer"
          inputMode="numeric"
          autoComplete="off"
          className="w-20"
          value={answer}
          onChange={(e) => setAnswer(e.target.value.replace(/\D/g, '').slice(0, 2))}
          aria-invalid={answer !== '' && !solved}
        />
        <Button type="button" size="icon" variant="ghost" onClick={refresh} aria-label={t('v2.login.captchaNew')} title={t('v2.login.captchaNew')}>
          <RefreshCw aria-hidden />
        </Button>
        {solved && (
          <span className="flex items-center gap-1 text-sm text-success">
            <CircleCheck className="size-4" aria-hidden />
            {t('v2.login.captchaSolved')}
          </span>
        )}
      </div>
      <p className="text-xs text-muted-foreground">{t('v2.login.captchaNote')}</p>
    </div>
  )
}
