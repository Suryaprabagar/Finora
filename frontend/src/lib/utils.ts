import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Format currency in INR by default */
export function formatCurrency(
  amount: number,
  currency: string = 'INR',
  symbol: string = '₹'
): string {
  if (currency === 'INR') {
    // Indian number formatting (lakhs/crores)
    const absAmount = Math.abs(amount)
    const formatted = new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(absAmount)
    return `${amount < 0 ? '-' : ''}${symbol}${formatted}`
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount)
}

/** Format large numbers in compact form: 12,50,000 → ₹12.5L */
export function formatCompact(amount: number, symbol: string = '₹'): string {
  const abs = Math.abs(amount)
  const sign = amount < 0 ? '-' : ''
  if (abs >= 10_000_000) return `${sign}${symbol}${(abs / 10_000_000).toFixed(1)}Cr`
  if (abs >= 100_000) return `${sign}${symbol}${(abs / 100_000).toFixed(1)}L`
  if (abs >= 1_000) return `${sign}${symbol}${(abs / 1_000).toFixed(1)}K`
  return `${sign}${symbol}${abs.toFixed(0)}`
}

/** Format date to DD MMM YYYY */
export function formatDate(dateStr: string | Date): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

/** Format date to MMM YYYY */
export function formatMonthYear(dateStr: string | Date): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

/** Get initials from full name */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

/** Calculate percentage */
export function calcPercentage(value: number, total: number): number {
  if (total === 0) return 0
  return Math.round((value / total) * 100)
}

/** Get month name */
export function getMonthName(month: number): string {
  const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return names[month - 1] || ''
}

/** Truncate string */
export function truncate(str: string, len: number): string {
  if (str.length <= len) return str
  return str.slice(0, len) + '...'
}

/** Get status chip class */
export function getStatusClass(status: string): string {
  switch (status.toLowerCase()) {
    case 'cleared':
    case 'active':
    case 'paid':
    case 'completed':
    case 'approved':
      return 'chip-cleared'
    case 'pending':
    case 'pending_renewal':
      return 'chip-pending'
    case 'overdue':
    case 'rejected':
    case 'expired':
    case 'cancelled':
      return 'chip-overdue'
    default:
      return 'chip-pending'
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function debounce<T extends (...args: any[]) => any>(fn: T, delay: number) {
  let timer: ReturnType<typeof setTimeout>
  const debounced = (...args: Parameters<T>) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
  debounced.cancel = () => clearTimeout(timer)
  return debounced
}
