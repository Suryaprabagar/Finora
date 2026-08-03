'use client'

import { useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { getInitials } from '@/lib/utils'

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/transactions': 'Transactions',
  '/income': 'Income',
  '/expenses': 'Expenses',
  '/budget': 'Budget',
  '/bank-accounts': 'Bank Accounts',
  '/credit-cards': 'Credit Cards',
  '/investments': 'Investments',
  '/loans': 'Loans',
  '/assets': 'Assets',
  '/insurance': 'Insurance',
  '/bills': 'Bills',
  '/goals': 'Goals',
  '/reports': 'Reports',
  '/settings': 'Settings',
}

function Icon({ name, size = 22, className = '' }: { name: string; size?: number; className?: string }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      style={{ fontSize: size }}
    >
      {name}
    </span>
  )
}

export function TopBar() {
  const pathname = usePathname()
  const router = useRouter()
  const { toggleSidebar } = useUIStore()
  const { user, logout } = useAuthStore()
  const [showDropdown, setShowDropdown] = useState(false)

  const title = pageTitles[pathname] ?? 'Finora'


  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <header className="h-16 fixed top-0 right-0 left-0 lg:left-60 z-30 flex items-center justify-between px-5 sm:px-6"
      style={{
        background: 'rgba(255,248,245,0.85)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: '1px solid #E7E2DB',
      }}
    >
      <div className="flex items-center gap-3">
        {/* Mobile hamburger */}
        <button
          onClick={toggleSidebar}
          className="lg:hidden p-2 -ml-1 rounded-lg text-[#51443c] hover:bg-[#f6ece7] transition-colors"
          aria-label="Toggle sidebar"
        >
          <Icon name="menu" size={22} />
        </button>

        <h2 className="font-bold text-[20px] text-[#1f1b18] hidden sm:block" style={{ fontFamily: 'Geist, sans-serif' }}>
          {title}
        </h2>
      </div>

      {/* User avatar + dropdown */}
      <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center gap-1.5 pl-1 pr-2 py-1 rounded-full hover:bg-[#f6ece7] transition-colors"
          >
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-[13px] text-white"
              style={{ background: '#6f4627', fontFamily: 'Geist, sans-serif' }}
            >
              {user ? getInitials(user.full_name) : 'U'}
            </div>
            <span className="material-symbols-outlined text-[#51443c]" style={{ fontSize: 18 }}>
              {showDropdown ? 'expand_less' : 'expand_more'}
            </span>
          </button>

          {showDropdown && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowDropdown(false)} />
              <div
                className="absolute right-0 top-full mt-2 w-52 z-[60] rounded-xl overflow-hidden"
                style={{ background: 'white', border: '1px solid #E7E2DB', boxShadow: '0 8px 24px rgba(139,94,60,0.12)' }}
              >
                <div className="px-4 py-3 border-b border-[#E7E2DB]">
                  <p className="text-[13px] font-semibold text-[#1f1b18] truncate">{user?.full_name}</p>
                  <p className="text-[11px] text-[#51443c] truncate">{user?.email}</p>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => { router.push('/settings'); setShowDropdown(false) }}
                    className="w-full text-left px-4 py-2.5 text-[13px] text-[#1f1b18] hover:bg-[#f6ece7] flex items-center gap-2.5 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[#51443c]" style={{ fontSize: 18 }}>manage_accounts</span>
                    Profile & Settings
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2.5 text-[13px] text-red-600 hover:bg-red-50 flex items-center gap-2.5 transition-colors"
                  >
                    <span className="material-symbols-outlined text-red-500" style={{ fontSize: 18 }}>logout</span>
                    Sign out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
    </header>
  )
}
