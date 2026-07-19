import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: string
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
  className?: string
}

export function EmptyState({ icon = 'inbox', title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center p-12 text-center finora-card bg-surface-container-lowest", className)}>
      <div className="w-16 h-16 bg-surface-variant rounded-full flex items-center justify-center mb-4 text-on-surface-variant">
        <span className="material-symbols-outlined text-3xl">{icon}</span>
      </div>
      <h3 className="text-lg font-display font-semibold text-on-surface mb-2">{title}</h3>
      {description && <p className="text-sm text-on-surface-variant max-w-sm mb-6">{description}</p>}
      {action && (
        <button onClick={action.onClick} className="btn-primary">
          <span className="material-symbols-outlined text-[18px]">add</span>
          {action.label}
        </button>
      )}
    </div>
  )
}
