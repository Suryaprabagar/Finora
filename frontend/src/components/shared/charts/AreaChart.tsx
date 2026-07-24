'use client'

import React from 'react'

import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { formatCurrency } from '@/lib/utils'

interface AreaChartProps {
  data: Array<Record<string, unknown>>
  xKey: string
  areas: Array<{ key: string; label: string; color: string }>
  height?: number
  formatValue?: (v: number) => string
  formatTooltip?: (v: number) => string
}

export const AreaChart = React.memo(function AreaChart({
  data,
  xKey,
  areas,
  height = 300,
  formatValue = (v) => formatCurrency(v, 'INR', '₹'),
  formatTooltip = (v) => formatCurrency(v, 'INR', '₹'),
}: AreaChartProps) {
  return (
    <div style={{ height: `${height}px`, width: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsAreaChart
          data={data}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            {areas.map((area) => (
              <linearGradient key={`color-${area.key}`} id={`color-${area.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={area.color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={area.color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E7E2DB" />
          <XAxis
            dataKey={xKey}
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#51443c', fontSize: 12 }}
            dy={10}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#51443c', fontSize: 12 }}
            tickFormatter={formatValue}
            dx={-10}
          />
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
            formatter={(value: any, name: any) => {
              const area = areas.find(a => a.key === String(name))
              return [formatTooltip(Number(value) || 0), area?.label || String(name)]
            }}
          />
          {areas.map((area) => (
            <Area
              key={area.key}
              type="monotone"
              dataKey={area.key}
              stroke={area.color}
              strokeWidth={2}
              fillOpacity={1}
              fill={`url(#color-${area.key})`}
              activeDot={{ r: 6, strokeWidth: 0, fill: area.color }}
            />
          ))}
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  )
})
