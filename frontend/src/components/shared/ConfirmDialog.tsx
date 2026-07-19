'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { LoadingSpinner } from './LoadingSpinner'
import { cn } from '@/lib/utils'

interface ConfirmDialogProps {
  open: boolean
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
  variant?: 'danger' | 'default'
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  loading = false,
  variant = 'default',
}: ConfirmDialogProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(isOpen) => !isOpen && !loading && onCancel()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] animate-in fade-in" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-surface-container-lowest rounded-xl shadow-card-hover border border-outline-variant p-6 z-[101] animate-in zoom-in-95 fade-in">
          <Dialog.Title className="text-xl font-display font-bold text-on-surface mb-2">
            {title}
          </Dialog.Title>
          <Dialog.Description className="text-on-surface-variant text-sm mb-6">
            {description}
          </Dialog.Description>

          <div className="flex justify-end gap-3">
            <button
              onClick={onCancel}
              disabled={loading}
              className="btn-secondary"
            >
              {cancelLabel}
            </button>
            <button
              onClick={onConfirm}
              disabled={loading}
              className={cn(
                "btn-primary",
                variant === 'danger' && "bg-error hover:bg-error/90 text-white"
              )}
            >
              {loading ? <LoadingSpinner size="sm" color="white" /> : confirmLabel}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
