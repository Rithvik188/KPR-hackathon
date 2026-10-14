import { CircleAlert, CircleCheck, CircleX, Clock, Send } from 'lucide-react'

import type { AppStatus, DocStatus } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { useLang } from '@/i18n'
import { cn } from '@/lib/utils'

const DOC_STYLES: Record<DocStatus, { className: string; Icon: typeof CircleCheck }> = {
  accepted: { className: 'bg-success-soft text-success', Icon: CircleCheck },
  fixable: { className: 'bg-warning-soft text-warning', Icon: CircleAlert },
  invalid: { className: 'bg-danger-soft text-danger', Icon: CircleX },
}

const APP_STYLES: Record<AppStatus, { className: string; Icon: typeof CircleCheck }> = {
  submitted: { className: 'bg-secondary text-secondary-foreground', Icon: Clock },
  needs_fix: { className: 'bg-warning-soft text-warning', Icon: CircleAlert },
  ready_for_officer: { className: 'bg-accent text-accent-foreground', Icon: Send },
  approved: { className: 'bg-success-soft text-success', Icon: CircleCheck },
  rejected: { className: 'bg-danger-soft text-danger', Icon: CircleX },
}

export function DocStatusBadge({ status, className }: { status: DocStatus; className?: string }) {
  const { t } = useLang()
  const { className: tone, Icon } = DOC_STYLES[status]
  return (
    <Badge className={cn('h-6 gap-1.5 px-2.5 text-sm', tone, className)}>
      <Icon aria-hidden />
      {t(`status.${status}`)}
    </Badge>
  )
}

export function AppStatusBadge({ status, className }: { status: AppStatus; className?: string }) {
  const { t } = useLang()
  const { className: tone, Icon } = APP_STYLES[status]
  return (
    <Badge className={cn('h-6 gap-1.5 px-2.5 text-sm', tone, className)}>
      <Icon aria-hidden />
      {t(`app.${status}`)}
    </Badge>
  )
}
