'use client'

import { useState, useEffect } from 'react'
import { getTable1Metrics, type MetricsResponse, type PeriodsResponse } from '@/lib/api'

interface MetricsPreviewProps {
  periods: PeriodsResponse
  baseWeek: string
  onMetricsChange: (metrics: MetricsResponse | null) => void
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
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Cache key for localStorage
  const getCacheKey = (week: string) => `metrics_${week}`

  // Load metrics from cache or API
  const loadMetrics = async (forceRefresh = false) => {
    const cacheKey = getCacheKey(baseWeek)
    
    // Try to load from cache first (unless force refresh)
    if (!forceRefresh) {
      try {
        const cachedData = localStorage.getItem(cacheKey)
        if (cachedData) {
          const parsed = JSON.parse(cachedData)
          // Check if cache is less than 1 hour old
          const cacheAge = Date.now() - parsed.timestamp
          if (cacheAge < 60 * 60 * 1000) { // 1 hour
            setMetrics(parsed.data)
            onMetricsChange(parsed.data)
            return
          }
        }
      } catch (err) {
        console.warn('Failed to load from cache:', err)
      }
    }

    // Load from API
    setLoading(true)
    setError(null)
    
    try {
      const periodsList = ['actual', 'last_week', 'last_year', 'year_2023']
      const metricsData = await getTable1Metrics(baseWeek, periodsList, true) // Include YTD
      setMetrics(metricsData)
      onMetricsChange(metricsData)
      
      // Save to cache
      try {
        localStorage.setItem(cacheKey, JSON.stringify({
          data: metricsData,
          timestamp: Date.now()
        }))
      } catch (err) {
        console.warn('Failed to save to cache:', err)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
      onMetricsChange(null)
    } finally {
      setLoading(false)
    }
  }

  const fetchMetrics = async () => {
    await loadMetrics(false) // Use cache if available
  }

  const clearAllCache = () => {
    try {
      // Clear all metrics cache
      const keys = Object.keys(localStorage)
      keys.forEach(key => {
        if (key.startsWith('metrics_') || key.startsWith('markets_')) {
          localStorage.removeItem(key)
        }
      })
      
      // Clear current metrics
      setMetrics(null)
      onMetricsChange(null)
      
      // Reload data
      loadMetrics(true)
      
      console.log('All cache cleared')
    } catch (err) {
      console.error('Failed to clear cache:', err)
    }
  }

  const refreshData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Clear cache for this week (both metrics and markets)
      const cacheKey = getCacheKey(baseWeek)
      localStorage.removeItem(cacheKey)
      localStorage.removeItem(`markets_${baseWeek}`)
      
      // Clear server cache
      await fetch(`http://localhost:8000/api/cache/invalidate/${baseWeek}`, {
        method: 'POST'
      })
      
      // Load fresh data
      await loadMetrics(true) // Force refresh
    } catch (err) {
      setError('Failed to refresh data')
      console.error('Refresh error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (periods) {
      // Try to load from cache first, don't auto-fetch from API
      const cacheKey = getCacheKey(baseWeek)
      try {
        const cachedData = localStorage.getItem(cacheKey)
        if (cachedData) {
          const parsed = JSON.parse(cachedData)
          const cacheAge = Date.now() - parsed.timestamp
          if (cacheAge < 60 * 60 * 1000) { // 1 hour
            setMetrics(parsed.data)
            onMetricsChange(parsed.data)
            return
          }
        }
      } catch (err) {
        console.warn('Failed to load from cache:', err)
      }
      // If no valid cache, don't auto-load - wait for user to click "Load Data"
    }
  }, [periods, baseWeek, onMetricsChange])

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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading metrics...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800 text-sm">{error}</div>
        <button 
          onClick={fetchMetrics}
          className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
        >
          Try again
        </button>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <div className="text-blue-800 text-sm font-medium mb-2">
            No metrics data loaded
          </div>
          <div className="text-blue-600 text-xs mb-4">
            Click "Load Data" to fetch metrics for {baseWeek}
          </div>
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Load Data'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header with period dates */}
      <div className="bg-yellow-100 border border-yellow-200 rounded-lg p-4">
        <div className="flex justify-between items-center">
          <div className="text-sm font-medium text-yellow-800">
            {getPeriodDateRange('actual')}
          </div>
          <div className="flex items-center gap-2">
            {/* Cache status indicator */}
            <div className="text-xs text-yellow-700">
              {(() => {
                const cacheKey = getCacheKey(baseWeek)
                try {
                  const cachedData = localStorage.getItem(cacheKey)
                  if (cachedData) {
                    const parsed = JSON.parse(cachedData)
                    const cacheAge = Date.now() - parsed.timestamp
                    const ageMinutes = Math.floor(cacheAge / (60 * 1000))
                    return `Cached ${ageMinutes}m ago`
                  }
                } catch (err) {
                  // Ignore cache errors
                }
                return 'No cache'
              })()}
            </div>
            <button
              onClick={refreshData}
              disabled={loading}
              className="px-3 py-1 text-xs bg-yellow-200 hover:bg-yellow-300 text-yellow-800 rounded-md disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh Data'}
            </button>
            <button
              onClick={clearAllCache}
              className="px-3 py-1 text-xs bg-red-200 hover:bg-red-300 text-red-800 rounded-md"
            >
              Clear Cache
            </button>
          </div>
        </div>
      </div>

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
