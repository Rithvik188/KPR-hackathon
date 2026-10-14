import { Camera, Upload } from 'lucide-react'
import { type Ref, useState } from 'react'

import { useLang } from '@/i18n'
import { cn } from '@/lib/utils'

/**
 * Card-photo input. `capture="environment"` opens the rear camera on phones and a file picker on laptops.
 * Also accepts drag-and-drop. Pass `inputRef` so a Retake button can reopen the picker.
 */
export function UploadBox({
  onFile,
  disabled,
  inputRef,
  compact,
}: {
  onFile: (file: File) => void
  disabled?: boolean
  inputRef?: Ref<HTMLInputElement>
  compact?: boolean
}) {
  const { t } = useLang()
  const [dragging, setDragging] = useState(false)

  return (
    <label
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        const file = e.dataTransfer.files?.[0]
        if (file && !disabled) onFile(file)
      }}
      className={cn(
        'flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-input bg-background text-center transition-colors',
        'hover:border-primary/60 hover:bg-accent/40 focus-within:border-primary focus-within:ring-3 focus-within:ring-ring/30',
        compact ? 'px-3 py-4' : 'px-4 py-8',
        dragging && 'border-primary bg-accent/60',
        disabled && 'pointer-events-none opacity-50',
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png"
        capture="environment"
        className="sr-only"
        disabled={disabled}
        onChange={(e) => {
          const file = e.target.files?.[0]
          e.target.value = '' // allow choosing the same file again after a retake
          if (file) onFile(file)
        }}
      />
      <span className="flex items-center gap-2 text-primary">
        <Camera className="size-5" aria-hidden />
        <Upload className="size-5" aria-hidden />
      </span>
      <span className="font-medium">{t('counter.choose')}</span>
      {!compact && <span className="text-xs text-muted-foreground">{t('counter.chooseHint')}</span>}
    </label>
  )
}
