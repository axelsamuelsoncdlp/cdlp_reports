'use client'

import { useEffect } from 'react'
import { useMetrics, useDataCache } from '@/contexts/DataCacheContext'
import { type PeriodsResponse } from '@/lib/api'

interface MetricsPreviewProps {
  periods: PeriodsResponse
  baseWeek: string
  onMetricsChange: (metrics: any) => void
}

const METRIC_LABELS = [
  'Online Gross Revenue',
  'Returns',
  'Return Rate %',
  'Online Net Revenue',
  'Retail Concept Store',
  'Retail Pop-ups, Outlets',
  'Retail Net Revenue',
  'Wholesale Net Revenue',
  'Total Net Revenue',
  'Returning Customers',
  'New customers',
  'Marketing Spend',
  'Online Cost of Sale(3)'
]

const METRIC_KEYS = [
  'online_gross_revenue',
  'returns',
  'return_rate_pct',
  'online_net_revenue',
  'retail_concept_store',
  'retail_popups_outlets',
  'retail_net_revenue',
  'wholesale_net_revenue',
  'total_net_revenue',
  'returning_customers',
  'new_customers',
  'marketing_spend',
  'online_cost_of_sale_3'
]

export default function MetricsPreview({ 
  periods, 
  baseWeek, 
  onMetricsChange 
}: MetricsPreviewProps) {
  const { metrics } = useMetrics()
  const { refreshData, clearCache } = useDataCache()

  // Notify parent when metrics change
  useEffect(() => {
    onMetricsChange(metrics)
  }, [metrics, onMetricsChange])

  const calculateGrowthPercentage = (current: number, previous: number): number | null => {
    if (previous === 0) return null
    return ((current - previous) / previous) * 100
  }

  const formatGrowthPercentage = (value: number | null): string => {
    if (value === null) return '-'
    
    const absValue = Math.abs(value)
    const formatted = absValue.toFixed(1)
    
    if (value < 0) {
      return `(${formatted}%)`
    } else {
      return `${formatted}%`
    }
  }

  const formatValue = (value: number, metricKey: string): string => {
    if (metricKey === 'return_rate_pct' || metricKey === 'online_cost_of_sale_3') {
      return `${value.toFixed(1)}%`
    }
    
    // Customer counts should NOT be formatted in thousands
    if (metricKey === 'returning_customers' || metricKey === 'new_customers') {
      return Math.round(value).toLocaleString('sv-SE')
    }
    
    if (typeof value === 'number') {
      if (value === 0) {
        return '0'
      }
      
      // Convert to thousands and round to nearest integer
      const thousandsValue = value / 1000
      const roundedThousands = Math.round(thousandsValue)
      
      return roundedThousands.toLocaleString('sv-SE')
    }
    
    return value.toString()
  }

  const getPeriodDisplayName = (periodKey: string): string => {
    const mapping: Record<string, string> = {
      'actual': 'Actual',
      'last_week': 'Last Week',
      'last_year': 'Last Year',
      'year_2023': '2023'
    }
    return mapping[periodKey] || periodKey
  }

  const getPeriodDateRange = (periodKey: string): string => {
    const dateRange = periods.date_ranges[periodKey]
    return dateRange?.display || 'N/A'
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading metrics...</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Metrics table */}
      <div className="bg-gray-50 rounded-lg overflow-hidden overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-200 border-b">
              <th className="text-left py-2 px-2 font-medium text-gray-900" rowSpan={2}>(SEK '000)</th>
              <th className="text-center py-2 px-2 font-medium text-gray-900 bg-gray-200" colSpan={7}>
                Latest Week: {getPeriodDateRange('actual')}
              </th>
              <th className="text-center py-2 px-2 font-medium text-gray-900 bg-blue-100" colSpan={5}>
                Year-to-date
              </th>
            </tr>
            <tr className="bg-gray-200 border-b">
              <th className="text-right py-1 px-2 font-medium text-gray-900 bg-gray-400">Actual</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900">Last Week</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900">Last Year</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900">2023</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900">vs Last Week</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900">vs Last Year</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900">vs 2023</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900 bg-blue-200">YTD Actual</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900 bg-blue-50">YTD Last Year</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900 bg-blue-50">YTD 2023</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900 bg-blue-50">YTD vs Last Year</th>
              <th className="text-right py-1 px-2 font-medium text-gray-900 bg-blue-50">YTD vs 2023</th>
            </tr>
          </thead>
          <tbody>
            {METRIC_LABELS.map((label, index) => {
              const metricKey = METRIC_KEYS[index]
              return (
                <tr key={metricKey} className="border-b border-gray-200 last:border-b-0">
                  <td className="py-2 px-2 font-medium text-gray-900">{label}</td>
                  <td className="py-2 px-2 text-right text-gray-700 bg-gray-200 font-semibold">
                    {formatValue(metrics.periods.actual?.[metricKey] || 0, metricKey)}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700">
                    {formatValue(metrics.periods.last_week?.[metricKey] || 0, metricKey)}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700">
                    {formatValue(metrics.periods.last_year?.[metricKey] || 0, metricKey)}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700">
                    {formatValue(metrics.periods.year_2023?.[metricKey] || 0, metricKey)}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700">
                    {formatGrowthPercentage(calculateGrowthPercentage(
                      metrics.periods.actual?.[metricKey] || 0, 
                      metrics.periods.last_week?.[metricKey] || 0
                    ))}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700">
                    {formatGrowthPercentage(calculateGrowthPercentage(
                      metrics.periods.actual?.[metricKey] || 0, 
                      metrics.periods.last_year?.[metricKey] || 0
                    ))}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700">
                    {formatGrowthPercentage(calculateGrowthPercentage(
                      metrics.periods.actual?.[metricKey] || 0, 
                      metrics.periods.year_2023?.[metricKey] || 0
                    ))}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700 bg-blue-100 font-semibold">
                    {formatValue(metrics.periods.ytd_actual?.[metricKey] || 0, metricKey)}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700 bg-blue-50">
                    {formatValue(metrics.periods.ytd_last_year?.[metricKey] || 0, metricKey)}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700 bg-blue-50">
                    {formatValue(metrics.periods.ytd_2023?.[metricKey] || 0, metricKey)}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700 bg-blue-50">
                    {formatGrowthPercentage(calculateGrowthPercentage(
                      metrics.periods.ytd_actual?.[metricKey] || 0, 
                      metrics.periods.ytd_last_year?.[metricKey] || 0
                    ))}
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700 bg-blue-50">
                    {formatGrowthPercentage(calculateGrowthPercentage(
                      metrics.periods.ytd_actual?.[metricKey] || 0, 
                      metrics.periods.ytd_2023?.[metricKey] || 0
                    ))}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Summary info */}
      <div className="text-sm text-gray-600">
        <p>Showing metrics for base week: <span className="font-medium">{baseWeek}</span></p>
        <p>Data loaded for {Object.keys(metrics.periods).length} periods</p>
      </div>
    </div>
  )
}
