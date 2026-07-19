import { cn } from '@/lib/utils'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'primary' | 'white' | 'on-surface'
  className?: string
}

export function LoadingSpinner({ size = 'md', color = 'primary', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
    xl: 'w-16 h-16 border-4',
  }

  const colorClasses = {
    primary: 'border-primary border-t-transparent',
    white: 'border-white border-t-transparent',
    'on-surface': 'border-on-surface border-t-transparent',
  }

  return (
    <div className={cn("flex justify-center items-center", className)}>
      <div
        className={cn(
          "rounded-full animate-spin",
          sizeClasses[size],
          colorClasses[color]
        )}
      />
    </div>
  )
}
