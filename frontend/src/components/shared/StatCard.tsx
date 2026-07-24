import Link from 'next/link'

interface StatCardProps {
  title: string
  value: string | React.ReactNode
  subtitle?: string
  trend?: { value: number; label: string }
  icon?: string
  iconColor?: string
  iconBg?: string
  className?: string
  loading?: boolean
  href?: string
}

export function StatCard({
  title,
  value,
  subtitle,
  trend,
  icon,
  iconColor = '#6f4627',
  iconBg = '#ffdcc5',
  className = '',
  loading = false,
  href,
}: StatCardProps) {
  
  if (loading) {
    return (
      <div className={`rounded-xl p-5 ${className}`} style={{ background: 'white', border: '1px solid #E7E2DB', boxShadow: '0 1px 3px rgba(0,0,0,0.02), 0 4px 12px rgba(139,94,60,0.03)' }}>
        <div className="flex justify-between items-start mb-4">
          <div className="h-4 bg-[#ebe0db] rounded w-24 animate-pulse" />
          <div className="w-10 h-10 bg-[#ebe0db] rounded-xl animate-pulse" />
        </div>
        <div className="h-8 bg-[#ebe0db] rounded w-32 animate-pulse mb-2" />
        <div className="h-3 bg-[#ebe0db] rounded w-40 animate-pulse" />
      </div>
    )
  }

  const trendIsPositive = trend && trend.value > 0
  const trendIsNegative = trend && trend.value < 0

  const content = (
    <div
      className={`rounded-xl p-5 flex flex-col justify-between transition-all duration-200 ${className} ${href ? 'hover:border-primary cursor-pointer' : ''}`}
      style={{
        background: 'white',
        border: '1px solid #E7E2DB',
        boxShadow: '0 1px 3px rgba(0,0,0,0.02), 0 4px 12px rgba(139,94,60,0.03)',
        minHeight: 130,
      }}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <p className="text-[13px] font-medium" style={{ color: '#51443c' }}>{title}</p>
        {icon && (
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: iconBg }}
          >
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 20, color: iconColor, fontVariationSettings: "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 20" }}
            >
              {icon}
            </span>
          </div>
        )}
      </div>

      <div>
        <div className="flex items-baseline gap-2.5 mb-1">
          <span className="text-[28px] font-bold leading-none tracking-tight" style={{ fontFamily: 'Geist, sans-serif', color: '#1f1b18' }}>
            {value}
          </span>
          {trend && (
            <span
              className="text-[11px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-0.5"
              style={{
                background: trendIsPositive ? 'rgba(186,234,249,0.4)' : trendIsNegative ? 'rgba(186,26,26,0.08)' : 'rgba(235,224,219,0.5)',
                color: trendIsPositive ? '#265763' : trendIsNegative ? '#ba1a1a' : '#51443c',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 13 }}>
                {trendIsPositive ? 'trending_up' : trendIsNegative ? 'trending_down' : 'trending_flat'}
              </span>
              {Math.abs(trend.value)}%
            </span>
          )}
        </div>
        {subtitle && (
          <p className="text-[12px]" style={{ color: '#83746b' }}>{subtitle}</p>
        )}
      </div>
    </div>
  )

  if (href) {
    return <Link href={href} className="block">{content}</Link>
  }
  return content
}
