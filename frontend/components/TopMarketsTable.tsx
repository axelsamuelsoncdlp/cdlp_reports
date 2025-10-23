'use client'

import { useMarkets } from '@/contexts/DataCacheContext'
import { Skeleton } from '@/components/ui/skeleton'
import { Loader2 } from 'lucide-react'

interface TopMarketsTableProps {
  baseWeek: string
}

export default function TopMarketsTable({ baseWeek }: TopMarketsTableProps) {
  const { markets: marketsData } = useMarkets()

  const formatValue = (value: number): string => {
    if (value === 0) return '0'
    const thousandsValue = value / 1000
    const roundedThousands = Math.round(thousandsValue)
    return roundedThousands.toLocaleString('sv-SE')
  }

  const calculateYoY = (current: number, previous: number): number | null => {
    if (previous === 0) return null
    return ((current - previous) / previous) * 100
  }

  const formatYoY = (value: number | null): string => {
    if (value === null) return '-'
    const absValue = Math.abs(value)
    const formatted = Math.round(absValue).toString()
    if (value < 0) {
      return `(${formatted}%)`
    } else {
      return `${formatted}%`
    }
  }

  const calculateSoB = (marketValue: number, totalValue: number): number | null => {
    if (totalValue === 0) return null
    return (marketValue / totalValue) * 100
  }

  const formatSoB = (value: number | null): string => {
    if (value === null) return '-'
    return `${Math.round(value)}%`
  }

  const getWeekNumber = (weekStr: string): string => {
    const parts = weekStr.split('-')
    return `W${parts[1]}`
  }

  if (!marketsData || !marketsData.markets.length) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <span className="text-gray-600">Loading markets data...</span>
        </div>
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          {[...Array(15)].map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>
    )
  }

  const { markets, period_info } = marketsData
  const allWeekKeys = Object.keys(markets[0].weeks).sort()
  
  // Filter to only show 2025 weeks (current year)
  const weekKeys = allWeekKeys.filter(week => week.startsWith('2025'))
  
  // Debug logging
  console.log('🔍 TopMarkets Debug:', {
    totalMarkets: markets.length,
    firstMarket: markets[0].country,
    weekCount: weekKeys.length,
    weekKeys: weekKeys,
    sampleWeeks: markets[0].weeks,
    has2024Data: allWeekKeys.some(w => w.includes('2024'))
  })
  
  // Calculate last year weeks (same week numbers, previous year)
  const lastYearWeeks = weekKeys.map(week => {
    const [year, weekNum] = week.split('-')
    return `${parseInt(year) - 1}-${weekNum}`
  })
  
  console.log('🔍 Last Year Weeks:', lastYearWeeks)

  return (
    <div className="bg-gray-50 rounded-lg overflow-hidden overflow-x-auto">
      {/* Markets table */}
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-gray-200 border-b">
            <th className="text-left py-2 px-2 font-medium text-gray-900" rowSpan={3}>Country</th>
            <th className="text-center py-2 px-2 font-medium text-gray-900 bg-gray-200" colSpan={9}>
              Latest Week: {period_info.latest_dates}
            </th>
            <th className="text-center py-2 px-2 font-medium text-gray-900 bg-yellow-100" colSpan={9}>
              Y/Y GROWTH%
            </th>
            <th className="text-center py-2 px-2 font-medium text-gray-900 bg-green-100" colSpan={9}>
              SoB
            </th>
          </tr>
          <tr className="bg-gray-200 border-b">
            {weekKeys.map((week) => (
              <th key={week} className="text-right py-1 px-2 font-medium text-gray-900" rowSpan={2}>
                {getWeekNumber(week)}
              </th>
            ))}
            <th className="text-right py-1 px-2 font-medium text-gray-900 bg-blue-100" rowSpan={2}>Avg</th>
            {weekKeys.map((week) => (
              <th key={`yoy-${week}`} className="text-right py-1 px-2 font-medium text-gray-900 bg-yellow-50" rowSpan={2}>
                {getWeekNumber(week)}
              </th>
            ))}
            <th className="text-right py-1 px-2 font-medium text-gray-900 bg-yellow-50" rowSpan={2}>Avg</th>
            {weekKeys.map((week) => (
              <th key={`sob-${week}`} className="text-right py-1 px-2 font-medium text-gray-900 bg-green-50" rowSpan={2}>
                {getWeekNumber(week)}
              </th>
            ))}
            <th className="text-right py-1 px-2 font-medium text-gray-900 bg-green-50" rowSpan={2}>Avg</th>
          </tr>
        </thead>
        <tbody>
          {markets.map((market, index) => {
            const isRow = market.country === 'ROW'
            const isTotal = market.country === 'Total'
            const bgClass = isRow ? 'bg-gray-100' : isTotal ? 'bg-gray-200 font-semibold' : ''
            
            return (
              <tr key={index} className={`border-b border-gray-200 last:border-b-0 ${bgClass}`}>
                <td className={`py-2 px-2 font-medium text-gray-900 ${isTotal ? 'font-bold' : ''}`}>
                  {market.country}
                </td>
                {weekKeys.map((week) => (
                  <td key={week} className="py-2 px-2 text-right text-gray-700">
                    {formatValue(market.weeks[week] || 0)}
                  </td>
                ))}
                <td className="py-2 px-2 text-right text-gray-700 bg-blue-50 font-medium">
                  {formatValue(market.average)}
                </td>
                {weekKeys.map((week, weekIndex) => {
                  const lastYearWeek = lastYearWeeks[weekIndex]
                  const currentValue = market.weeks[week] || 0
                  const lastYearValue = market.weeks[lastYearWeek] || 0
                  const yoY = calculateYoY(currentValue, lastYearValue)
                  
                  // Debug for first market
                  if (index === 0 && weekIndex === 0) {
                    console.log('🔍 YoY Calculation Debug:', {
                      week,
                      lastYearWeek,
                      currentValue,
                      lastYearValue,
                      yoY,
                      hasLastYearData: lastYearWeek in market.weeks
                    })
                  }
                  
                  return (
                    <td key={`yoy-${week}`} className="py-2 px-2 text-right text-gray-700 bg-yellow-50">
                      {formatYoY(yoY)}
                    </td>
                  )
                })}
                <td className="py-2 px-2 text-right text-gray-700 bg-yellow-50 font-medium">
                  {(() => {
                    // Calculate average YoY
                    let totalYoY = 0
                    let validWeeks = 0
                    weekKeys.forEach((week, weekIndex) => {
                      const lastYearWeek = lastYearWeeks[weekIndex]
                      const currentValue = market.weeks[week] || 0
                      const lastYearValue = market.weeks[lastYearWeek] || 0
                      const yoY = calculateYoY(currentValue, lastYearValue)
                      if (yoY !== null) {
                        totalYoY += yoY
                        validWeeks++
                      }
                    })
                    const avgYoY = validWeeks > 0 ? totalYoY / validWeeks : null
                    return formatYoY(avgYoY)
                  })()}
                </td>
                {weekKeys.map((week) => {
                  // Find total value for this week
                  const totalRow = markets.find(m => m.country === 'Total')
                  const totalValue = totalRow?.weeks[week] || 0
                  const marketValue = market.weeks[week] || 0
                  
                  // For Total row, show 100%, otherwise calculate SoB
                  const sob = isTotal ? 100 : calculateSoB(marketValue, totalValue)
                  
                  return (
                    <td key={`sob-${week}`} className="py-2 px-2 text-right text-gray-700 bg-green-50">
                      {formatSoB(sob)}
                    </td>
                  )
                })}
                <td className="py-2 px-2 text-right text-gray-700 bg-green-50 font-medium">
                  {(() => {
                    // For Total row, show 100%, otherwise calculate average SoB
                    if (isTotal) {
                      return formatSoB(100)
                    }
                    
                    // Calculate average SoB by averaging market share first, then converting to percentage
                    // This ensures the sum of all markets' avg SoB equals 100%
                    const totalRow = markets.find(m => m.country === 'Total')
                    let totalMarketValue = 0
                    let totalTotalValue = 0
                    
                    weekKeys.forEach(week => {
                      const totalValue = totalRow?.weeks[week] || 0
                      const marketValue = market.weeks[week] || 0
                      totalMarketValue += marketValue
                      totalTotalValue += totalValue
                    })
                    
                    const avgSoB = totalTotalValue > 0 ? (totalMarketValue / totalTotalValue) * 100 : null
                    return formatSoB(avgSoB)
                  })()}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

