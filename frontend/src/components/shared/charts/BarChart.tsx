'use client'

import React from 'react'

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { formatCurrency } from '@/lib/utils'

interface BarChartProps {
  data: Array<Record<string, unknown>>
  xKey: string
  bars: Array<{ key: string; label: string; color: string }>
  height?: number
  formatValue?: (v: number) => string
}

export const BarChart = React.memo(function BarChart({
  data,
  xKey,
  bars,
  height = 300,
  formatValue = (v) => formatCurrency(v, 'INR', '₹'),
}: BarChartProps) {
  return (
    <div style={{ height: `${height}px`, width: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChart
          data={data}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
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
            cursor={{ fill: '#f6ece7', opacity: 0.5 }}
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
              const bar = bars.find(b => b.key === String(name))
              return [formatValue(Number(value) || 0), bar?.label || String(name)]
            }}
          />
          <Legend 
            wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
            formatter={(value) => {
              const bar = bars.find(b => b.key === value)
              return <span className="text-on-surface-variant font-medium ml-1">{bar?.label || value}</span>
            }}
          />
          {bars.map((bar) => (
            <Bar
              key={bar.key}
              dataKey={bar.key}
              fill={bar.color}
              radius={[4, 4, 0, 0]}
              barSize={20}
            />
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  )
})
