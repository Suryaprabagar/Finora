'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { cn } from '@/lib/utils'

const navItems = [
  { name: 'Dashboard', href: '/', icon: 'home' },
  { name: 'Transactions', href: '/transactions', icon: 'swap_horiz' },
  { name: 'Income', href: '/income', icon: 'trending_up' },
  { name: 'Expenses', href: '/expenses', icon: 'receipt_long' },
  { name: 'Budget', href: '/budget', icon: 'account_balance_wallet' },
  { name: 'Bank Accounts', href: '/bank-accounts', icon: 'account_balance' },
  { name: 'Credit Cards', href: '/credit-cards', icon: 'credit_card' },
  { name: 'Investments', href: '/investments', icon: 'show_chart' },
  { name: 'Loans', href: '/loans', icon: 'handshake' },
  { name: 'Assets', href: '/assets', icon: 'home_work' },
  { name: 'Insurance', href: '/insurance', icon: 'shield' },
  { name: 'Bills', href: '/bills', icon: 'calendar_month' },
  { name: 'Goals', href: '/goals', icon: 'flag' },
  { name: 'Reports', href: '/reports', icon: 'bar_chart' },
  { name: 'Settings', href: '/settings', icon: 'settings' },
]

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, setSidebarOpen } = useUIStore()
  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 lg:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 h-screen w-60 flex flex-col transition-transform duration-300 ease-in-out",
          "bg-white border-r border-[#E7E2DB]",
          !sidebarOpen && "-translate-x-full lg:translate-x-0"
        )}
        style={{ boxShadow: '1px 0 0 0 #E7E2DB' }}
      >
        {/* Brand */}
        <div className="h-16 flex items-center px-5 border-b border-[#E7E2DB] shrink-0">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-9 h-9 bg-[#6f4627] rounded-xl flex items-center justify-center shadow-sm">
              <span className="font-bold text-white text-lg leading-none" style={{ fontFamily: 'Geist, sans-serif' }}>F</span>
            </div>
            <div>
              <p className="font-bold text-[17px] text-[#1f1b18] leading-tight" style={{ fontFamily: 'Geist, sans-serif' }}>Finora</p>
              <p className="text-[9px] text-[#51443c] uppercase tracking-widest font-medium">Personal Finance</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-3 space-y-0.5 custom-scrollbar">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-[13.5px] font-medium transition-all duration-150",
                  isActive
                    ? "text-[#6f4627] bg-[#ffdcc5]/40"
                    : "text-[#51443c] hover:bg-[#f6ece7] hover:text-[#1f1b18]"
                )}
              >
                <span
                  className="material-symbols-outlined"
                  style={{
                    fontSize: '20px',
                    fontVariationSettings: isActive
                      ? "'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 20"
                      : "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 20",
                    color: isActive ? '#6f4627' : undefined,
                    flexShrink: 0,
                  }}
                >
                  {item.icon}
                </span>
                <span className="truncate">{item.name}</span>
                {isActive && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-[#6f4627]" />
                )}
              </Link>
            )
          })}
        </nav>
      </aside>
    </>
  )
}
