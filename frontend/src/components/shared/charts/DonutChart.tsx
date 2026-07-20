'use client'

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { formatCurrency } from '@/lib/utils'

interface DonutChartProps {
  data: Array<{ name: string; value: number; color: string }>
  height?: number
  showLegend?: boolean
  centerLabel?: string
  centerValue?: string
  formatValue?: (v: number) => string
}

export function DonutChart({
  data,
  height = 300,
  showLegend = true,
  centerLabel,
  centerValue,
  formatValue = (v) => formatCurrency(v, 'INR', '₹'),
}: DonutChartProps) {
  const total = data.reduce((acc, item) => acc + item.value, 0)

  return (
    <div className="flex flex-col h-full w-full">
      <div className="relative" style={{ height: showLegend ? `${height - 100}px` : `${height}px` }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius="70%"
              outerRadius="90%"
              paddingAngle={2}
              dataKey="value"
              stroke="none"
              isAnimationActive={true}
              animationBegin={0}
              animationDuration={1000}
              animationEasing="ease-out"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                borderRadius: '8px',
                border: '1px solid #E7E2DB',
                boxShadow: '0px 4px 12px rgba(139,94,60,0.06)',
                fontFamily: 'Inter, sans-serif',
                fontSize: '14px',
              }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any) => formatValue(Number(value) || 0)}
            />
          </PieChart>
        </ResponsiveContainer>
        
        {(centerLabel || centerValue) && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            {centerLabel && <p className="text-xs text-on-surface-variant font-medium">{centerLabel}</p>}
            {centerValue && <p className="text-2xl font-display font-bold text-on-surface mt-1">{centerValue}</p>}
          </div>
        )}
      </div>

      {showLegend && (
        <div className="mt-4 px-2 overflow-y-auto custom-scrollbar max-h-[100px]">
          <ul className="space-y-2">
            {data.map((item, index) => {
              const percentage = total > 0 ? Math.round((item.value / total) * 100) : 0
              return (
                <li key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                    <span className="text-on-surface font-medium truncate max-w-[120px]">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-3 text-on-surface-variant">
                    <span>{formatValue(item.value)}</span>
                    <span className="w-8 text-right font-medium">{percentage}%</span>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
