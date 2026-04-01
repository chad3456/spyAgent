import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Shield, Percent, AlertCircle, RefreshCw } from 'lucide-react'
import { fetchDefenseData } from '../api/client'
import type { TimeSeriesPoint } from '../types'
import MetricCard from './MetricCard'
import NewsCard from './NewsCard'
import ChartCard from './ChartCard'
import { SectionSkeleton } from './LoadingSkeleton'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getLastValue(series: TimeSeriesPoint[]): number | null {
  if (!series || series.length === 0) return null
  const filtered = series.filter((p) => p.value !== null)
  if (filtered.length === 0) return null
  return filtered[filtered.length - 1].value
}

function getTrend(series: TimeSeriesPoint[]): number | null {
  const filtered = series.filter((p) => p.value !== null)
  if (filtered.length < 2) return null
  const prev = filtered[filtered.length - 2].value!
  const curr = filtered[filtered.length - 1].value!
  if (prev === 0) return null
  return ((curr - prev) / Math.abs(prev)) * 100
}

function getLastYear(series: TimeSeriesPoint[]): number | null {
  const filtered = series.filter((p) => p.value !== null)
  if (filtered.length === 0) return null
  return filtered[filtered.length - 1].year
}

function last5(series: TimeSeriesPoint[]): Array<{ year: number; value: number }> {
  return series
    .filter((p): p is { year: number; value: number } => p.value !== null)
    .slice(-5)
}

function formatBillions(value: number | null): string {
  if (value === null) return '—'
  // World Bank returns current USD — convert
  if (value > 1e9) return `$${(value / 1e9).toFixed(1)}B`
  if (value > 1e6) return `$${(value / 1e6).toFixed(0)}M`
  return `$${value.toFixed(2)}`
}

// ─── Custom tooltip ───────────────────────────────────────────────────────────

const DarkTooltip = ({
  active,
  payload,
  label,
  unit = '',
}: {
  active?: boolean
  payload?: Array<{ value: number; color: string; name: string }>
  label?: string
  unit?: string
}) => {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="bg-[#0d1b2e] border border-[#1e3a5f] rounded-lg p-3 shadow-xl text-sm">
      <p className="text-[#8ba3c0] mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }} className="font-semibold">
          {entry.name}: {entry.value.toFixed(2)}{unit}
        </p>
      ))}
    </div>
  )
}

const BillionTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ value: number; color: string; name: string }>
  label?: string
}) => {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="bg-[#0d1b2e] border border-[#1e3a5f] rounded-lg p-3 shadow-xl text-sm">
      <p className="text-[#8ba3c0] mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }} className="font-semibold">
          {entry.name}: {formatBillions(entry.value)}
        </p>
      ))}
    </div>
  )
}

// ─── Error state ──────────────────────────────────────────────────────────────

const ErrorState: React.FC<{ message: string; onRetry: () => void }> = ({
  message,
  onRetry,
}) => (
  <div className="flex flex-col items-center justify-center py-16 gap-4">
    <AlertCircle className="w-12 h-12 text-red-400" />
    <div className="text-center">
      <p className="text-[#e8f0fe] font-semibold mb-1">Failed to load defence data</p>
      <p className="text-[#8ba3c0] text-sm">{message}</p>
    </div>
    <button
      onClick={onRetry}
      className="flex items-center gap-2 px-4 py-2 bg-[#FF9933]/20 text-[#FF9933] border border-[#FF9933]/40 rounded-lg hover:bg-[#FF9933]/30 transition-colors text-sm font-medium"
    >
      <RefreshCw className="w-4 h-4" />
      Retry
    </button>
  </div>
)

// ─── Main component ───────────────────────────────────────────────────────────

const DefenseSection: React.FC = () => {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['defense'],
    queryFn: fetchDefenseData,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <SectionSkeleton />
  if (isError) {
    const msg = error instanceof Error ? error.message : 'Unknown error'
    return <ErrorState message={msg} onRetry={() => refetch()} />
  }
  if (!data) return null

  const militaryLast = getLastValue(data.militaryExpenditure)
  const militaryTrend = getTrend(data.militaryExpenditure)
  const militaryYear = getLastYear(data.militaryExpenditure)

  const gdpPctLast = getLastValue(data.militaryGdpPercent)
  const gdpPctTrend = getTrend(data.militaryGdpPercent)
  const gdpPctYear = getLastYear(data.militaryGdpPercent)

  const militaryData = last5(data.militaryExpenditure)
  const gdpPctData = last5(data.militaryGdpPercent)

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Military Expenditure"
          value={formatBillions(militaryLast)}
          subtitle={militaryYear ? `FY ${militaryYear}` : undefined}
          trend={militaryTrend}
          trendLabel="YoY"
          icon={Shield}
          accentColor="saffron"
          source="World Bank / SIPRI"
          isLive
        />
        <MetricCard
          title="Military % of GDP"
          value={gdpPctLast !== null ? `${gdpPctLast.toFixed(2)}%` : '—'}
          subtitle={gdpPctYear ? `FY ${gdpPctYear}` : undefined}
          trend={gdpPctTrend}
          trendLabel="YoY"
          icon={Percent}
          accentColor="green"
          source="World Bank"
          isLive
        />
        {/* Context cards */}
        <div className="card gradient-border-saffron col-span-2 flex flex-col justify-center gap-2">
          <p className="text-[#8ba3c0] text-xs font-medium uppercase tracking-wider">
            Defence Context
          </p>
          <p className="text-[#e8f0fe] text-sm leading-relaxed">
            India is the world's 4th largest military spender. With an ambitious indigenisation
            programme, it targets 68% domestic procurement under Aatmanirbhar Bharat.
          </p>
          <p className="text-[#8ba3c0] text-[10px]">Source: Ministry of Defence, SIPRI</p>
        </div>
      </div>

      {/* Charts + News */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Charts */}
        <div className="xl:col-span-2 space-y-6">
          {/* Military expenditure line chart */}
          <ChartCard
            title="Military Expenditure (USD)"
            source="World Bank / SIPRI"
            minHeight={220}
          >
            {militaryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart
                  data={militaryData}
                  margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                  <XAxis
                    dataKey="year"
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={{ stroke: '#1e3a5f' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={52}
                    tickFormatter={(v) => {
                      if (v >= 1e9) return `$${(v / 1e9).toFixed(0)}B`
                      if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`
                      return `$${v}`
                    }}
                  />
                  <Tooltip content={<BillionTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#FF9933"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: '#FF9933', strokeWidth: 0 }}
                    activeDot={{ r: 6, fill: '#FF9933' }}
                    name="Expenditure"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-[#8ba3c0] text-sm">
                No data available
              </div>
            )}
          </ChartCard>

          {/* Military % GDP area chart */}
          <ChartCard
            title="Military Expenditure (% of GDP)"
            source="World Bank"
            minHeight={220}
          >
            {gdpPctData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart
                  data={gdpPctData}
                  margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                >
                  <defs>
                    <linearGradient id="militaryGdpGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#138808" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#138808" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
                  <XAxis
                    dataKey="year"
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={{ stroke: '#1e3a5f' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#8ba3c0', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `${v}%`}
                    width={40}
                  />
                  <Tooltip content={<DarkTooltip unit="%" />} />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#138808"
                    strokeWidth={2.5}
                    fill="url(#militaryGdpGradient)"
                    name="% of GDP"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-[#8ba3c0] text-sm">
                No data available
              </div>
            )}
          </ChartCard>

          {/* SIPRI context table */}
          <div className="card">
            <h3 className="text-[#e8f0fe] font-semibold text-sm mb-4">
              Global Military Ranking Context
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1e3a5f]">
                    <th className="text-left py-2 text-[#8ba3c0] text-xs font-medium">Rank</th>
                    <th className="text-left py-2 text-[#8ba3c0] text-xs font-medium">Country</th>
                    <th className="text-right py-2 text-[#8ba3c0] text-xs font-medium">Spending</th>
                    <th className="text-right py-2 text-[#8ba3c0] text-xs font-medium">% GDP</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { rank: 1, country: '🇺🇸 USA', spending: '$916B', pct: '3.4%' },
                    { rank: 2, country: '🇨🇳 China', spending: '$296B', pct: '1.7%' },
                    { rank: 3, country: '🇷🇺 Russia', spending: '$109B', pct: '5.9%' },
                    { rank: 4, country: '🇮🇳 India', spending: `${formatBillions(militaryLast)}`, pct: gdpPctLast !== null ? `${gdpPctLast.toFixed(2)}%` : '2.4%' },
                    { rank: 5, country: '🇸🇦 Saudi Arabia', spending: '$76B', pct: '6.0%' },
                  ].map((row) => (
                    <tr
                      key={row.rank}
                      className={`border-b border-[#1e3a5f]/50 ${row.rank === 4 ? 'bg-[#FF9933]/5' : ''}`}
                    >
                      <td className="py-2.5 text-[#8ba3c0] text-xs">{row.rank}</td>
                      <td className={`py-2.5 text-sm ${row.rank === 4 ? 'text-[#FF9933] font-semibold' : 'text-[#e8f0fe]'}`}>
                        {row.country}
                      </td>
                      <td className="py-2.5 text-right text-[#e8f0fe] font-mono text-xs metric-value">
                        {row.spending}
                      </td>
                      <td className="py-2.5 text-right text-[#8ba3c0] text-xs">
                        {row.pct}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-[#8ba3c0] text-[10px] mt-2">
                SIPRI data 2023 estimates · India row uses live API data
              </p>
            </div>
          </div>
        </div>

        {/* News feed */}
        <div className="xl:col-span-1">
          <div className="sticky top-4">
            <h3 className="text-[#e8f0fe] font-semibold text-sm mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full" />
              Defence News
            </h3>
            {data.news && data.news.length > 0 ? (
              <div className="space-y-3 max-h-[900px] overflow-y-auto pr-1">
                {data.news.slice(0, 12).map((item, i) => (
                  <NewsCard key={i} item={item} compact />
                ))}
              </div>
            ) : (
              <div className="card text-center text-[#8ba3c0] text-sm py-8">
                No news available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default DefenseSection
